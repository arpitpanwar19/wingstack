import os
import sqlite3
import uuid
import json
from contextlib import asynccontextmanager, closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / '.env')

GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '').strip()
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '').strip()
DATABASE_PATH = Path(os.getenv('DATABASE_PATH', str(BACKEND_DIR / 'wingstack.sqlite3')))
JWT_ISSUER = 'wingstack-api'
JWT_LIFETIME = timedelta(days=7)

if not GOOGLE_CLIENT_ID:
    raise RuntimeError('Set GOOGLE_CLIENT_ID in backend/.env before starting the API.')
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError('Set JWT_SECRET_KEY to at least 32 characters in backend/.env.')


class GoogleCredentialRequest(BaseModel):
    credential: str = Field(min_length=16, max_length=8192)


def connect_database():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with closing(connect_database()) as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                google_subject TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                streak_days INTEGER NOT NULL DEFAULT 0,
                profile_json TEXT NOT NULL DEFAULT '{}'
            )
            '''
        )
        columns = {
            row['name']
            for row in connection.execute('PRAGMA table_info(students)')
        }
        if 'profile_json' not in columns:
            connection.execute(
                "ALTER TABLE students ADD COLUMN profile_json TEXT NOT NULL DEFAULT '{}'"
            )
        connection.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield


app = FastAPI(title='WingStack Student Auth API', lifespan=lifespan)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173',
    ).split(',')
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['Authorization', 'Content-Type'],
)


def user_from_verified_claims(claims):
    email_claim = claims.get('email')
    if not isinstance(email_claim, str) or not email_claim.strip():
        raise HTTPException(status_code=401, detail='Google did not provide an email address.')
    email = email_claim.strip().lower()
    if claims.get('email_verified') is not True:
        raise HTTPException(status_code=403, detail='Verify your Google email before signing in.')
    if not email.endswith('@gmail.com'):
        raise HTTPException(status_code=403, detail='Use a verified @gmail.com account to sign in.')

    google_subject = claims.get('sub')
    if not google_subject:
        raise HTTPException(status_code=401, detail='Google did not provide a valid account ID.')

    return {
        'google_subject': google_subject,
        'email': email,
        'name': claims.get('name') or email.split('@', maxsplit=1)[0],
    }


def public_user(row):
    profile = {}
    try:
        profile = json.loads(row['profile_json'] or '{}')
    except (json.JSONDecodeError, KeyError, sqlite3.Error):
        profile = {}

    return {
        'id': row['id'],
        'name': profile.get('name') or row['name'],
        'email': row['email'],
        'role': 'student',
        'targetRole': profile.get('targetRole', 'Student'),
        'streakDays': row['streak_days'],
        **profile,
    }


def create_access_token(student_id):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            'sub': student_id,
            'iss': JWT_ISSUER,
            'iat': now,
            'exp': now + JWT_LIFETIME,
        },
        JWT_SECRET_KEY,
        algorithm='HS256',
    )


def get_current_student(
    authorization: Annotated[str | None, Header()] = None,
):
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail='Sign in with Google to continue.')

    access_token = authorization.split(maxsplit=1)[1]
    try:
        token_data = jwt.decode(
            access_token,
            JWT_SECRET_KEY,
            algorithms=['HS256'],
            issuer=JWT_ISSUER,
            options={'require': ['exp', 'iat', 'iss', 'sub']},
        )
    except jwt.PyJWTError as error:
        raise HTTPException(status_code=401, detail='Your session has expired. Sign in again.') from error

    with closing(connect_database()) as connection:
        student = connection.execute(
            'SELECT * FROM students WHERE id = ?',
            (token_data['sub'],),
        ).fetchone()

    if student is None:
        raise HTTPException(status_code=401, detail='Student account not found. Sign in again.')
    return public_user(student)


@app.get('/health')
def health_check():
    return {'status': 'ok'}


@app.post('/api/auth/google')
def sign_in_with_google(payload: GoogleCredentialRequest):
    try:
        claims = id_token.verify_oauth2_token(
            payload.credential,
            GoogleRequest(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as error:
        raise HTTPException(status_code=401, detail='Google credential is invalid or expired.') from error
    except GoogleAuthError as error:
        raise HTTPException(status_code=503, detail='Google account verification is temporarily unavailable.') from error

    identity = user_from_verified_claims(claims)
    now = datetime.now(timezone.utc).isoformat()
    student_id = uuid.uuid4().hex

    try:
        with closing(connect_database()) as connection:
            student = connection.execute(
                'SELECT * FROM students WHERE google_subject = ?',
                (identity['google_subject'],),
            ).fetchone()
            if student:
                connection.execute(
                    'UPDATE students SET email = ?, name = ? WHERE id = ?',
                    (identity['email'], identity['name'], student['id']),
                )
                student_id = student['id']
            else:
                connection.execute(
                    '''
                    INSERT INTO students (id, google_subject, email, name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        student_id,
                        identity['google_subject'],
                        identity['email'],
                        identity['name'],
                        now,
                    ),
                )
            connection.commit()
            student = connection.execute(
                'SELECT * FROM students WHERE id = ?',
                (student_id,),
            ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail='This Gmail address is already linked to another student account.',
        ) from error

    return {
        'access_token': create_access_token(student_id),
        'token_type': 'bearer',
        'user': public_user(student),
    }


@app.get('/api/auth/me')
def get_student_profile(
    student: Annotated[dict, Depends(get_current_student)],
):
    return student


@app.put('/api/users/profile')
def update_student_profile(
    payload: dict,
    student: Annotated[dict, Depends(get_current_student)],
):
    with closing(connect_database()) as connection:
        row = connection.execute(
            'SELECT * FROM students WHERE id = ?',
            (student['id'],),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail='Student account not found. Sign in again.')

        try:
            profile = json.loads(row['profile_json'] or '{}')
        except (json.JSONDecodeError, KeyError, sqlite3.Error):
            profile = {}
        if not isinstance(profile, dict):
            profile = {}

        profile.update(payload)
        name = profile.get('name')
        if isinstance(name, str) and name.strip():
            connection.execute(
                'UPDATE students SET name = ?, profile_json = ? WHERE id = ?',
                (name.strip(), json.dumps(profile), student['id']),
            )
        else:
            connection.execute(
                'UPDATE students SET profile_json = ? WHERE id = ?',
                (json.dumps(profile), student['id']),
            )
        connection.commit()

        updated = connection.execute(
            'SELECT * FROM students WHERE id = ?',
            (student['id'],),
        ).fetchone()

    return {'user': public_user(updated)}
