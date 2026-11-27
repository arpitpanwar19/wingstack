import unittest

from fastapi import HTTPException

from main import user_from_verified_claims


class GoogleStudentIdentityTests(unittest.TestCase):
    def test_accepts_verified_gmail_and_normalizes_address(self):
        identity = user_from_verified_claims(
            {
                'email': 'Student@GMAIL.com',
                'email_verified': True,
                'sub': 'google-subject',
                'name': 'Student Name',
            }
        )

        self.assertEqual(identity['email'], 'student@gmail.com')
        self.assertEqual(identity['google_subject'], 'google-subject')

    def test_rejects_unverified_gmail(self):
        with self.assertRaises(HTTPException) as raised:
            user_from_verified_claims(
                {'email': 'student@gmail.com', 'email_verified': False, 'sub': 'subject'}
            )

        self.assertEqual(raised.exception.status_code, 403)

    def test_rejects_non_gmail_google_accounts(self):
        with self.assertRaises(HTTPException) as raised:
            user_from_verified_claims(
                {'email': 'student@example.com', 'email_verified': True, 'sub': 'subject'}
            )

        self.assertEqual(raised.exception.status_code, 403)


if __name__ == '__main__':
    unittest.main()
