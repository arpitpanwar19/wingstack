import os
import re
import time
import json
import asyncio
import httpx
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

_ATS_CACHE: dict = {"timestamp": 0.0, "jobs": []}
CACHE_TTL_SECONDS = 1800

DIRECT_BOARDS = [{'company': 'Razorpay', 'hq_or_india_hubs': ['Bengaluru', 'Remote'], 'category': 'Indian Unicorn', 'ats_type': 'greenhouse', 'slug': 'razorpaysoftwareprivatelimited', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/razorpaysoftwareprivatelimited/jobs?content=true', 'careers_page': 'https://razorpay.com/jobs/'}, {'company': 'CRED', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Indian Unicorn', 'ats_type': 'lever', 'slug': 'cred', 'fetch_method': 'http_get_json', 'api_url': 'https://api.lever.co/v0/postings/cred?mode=json', 'careers_page': 'https://careers.cred.club/'}, {'company': 'Postman', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Indian Unicorn', 'ats_type': 'greenhouse', 'slug': 'postman', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/postman/jobs?content=true', 'careers_page': 'https://www.postman.com/company/careers/'}, {'company': 'BrowserStack', 'hq_or_india_hubs': ['Mumbai', 'Remote'], 'category': 'Indian Unicorn', 'ats_type': 'greenhouse', 'slug': 'browserstack', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/browserstack/jobs?content=true', 'careers_page': 'https://www.browserstack.com/careers'}, {'company': 'Groww', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Indian Unicorn', 'ats_type': 'greenhouse', 'slug': 'groww', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/groww/jobs?content=true', 'careers_page': 'https://groww.in/careers'}, {'company': 'MoEngage', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Indian Startup', 'ats_type': 'greenhouse', 'slug': 'moengage', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/moengage/jobs?content=true', 'careers_page': 'https://www.moengage.com/careers/'}, {'company': 'Stripe', 'hq_or_india_hubs': ['Bengaluru', 'Remote'], 'category': 'Global Fintech', 'ats_type': 'greenhouse', 'slug': 'stripe', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true', 'careers_page': 'https://stripe.com/jobs'}, {'company': 'Airbnb', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'airbnb', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/airbnb/jobs?content=true', 'careers_page': 'https://careers.airbnb.com/'}, {'company': 'Coinbase', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Fintech', 'ats_type': 'greenhouse', 'slug': 'coinbase', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/coinbase/jobs?content=true', 'careers_page': 'https://www.coinbase.com/careers'}, {'company': 'Databricks', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global Data/AI', 'ats_type': 'greenhouse', 'slug': 'databricks', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/databricks/jobs?content=true', 'careers_page': 'https://www.databricks.com/company/careers'}, {'company': 'Cloudflare', 'hq_or_india_hubs': ['Bengaluru', 'Remote-India'], 'category': 'Global Infrastructure', 'ats_type': 'greenhouse', 'slug': 'cloudflare', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/cloudflare/jobs?content=true', 'careers_page': 'https://www.cloudflare.com/careers/'}, {'company': 'GitLab', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevTools', 'ats_type': 'greenhouse', 'slug': 'gitlab', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/gitlab/jobs?content=true', 'careers_page': 'https://about.gitlab.com/jobs/'}, {'company': 'Elastic', 'hq_or_india_hubs': ['Remote-India', 'Bengaluru'], 'category': 'Global Data/Search', 'ats_type': 'greenhouse', 'slug': 'elastic', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/elastic/jobs?content=true', 'careers_page': 'https://www.elastic.co/about/careers/'}, {'company': 'MongoDB', 'hq_or_india_hubs': ['Gurugram', 'Bengaluru', 'Remote-India'], 'category': 'Global Database', 'ats_type': 'greenhouse', 'slug': 'mongodb', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/mongodb/jobs?content=true', 'careers_page': 'https://www.mongodb.com/company/careers'}, {'company': 'Twilio', 'hq_or_india_hubs': ['Bengaluru', 'Remote-India'], 'category': 'Global CPaaS', 'ats_type': 'greenhouse', 'slug': 'twilio', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/twilio/jobs?content=true', 'careers_page': 'https://www.twilio.com/en-us/company/jobs'}, {'company': 'Okta', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global Security', 'ats_type': 'greenhouse', 'slug': 'okta', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/okta/jobs?content=true', 'careers_page': 'https://www.okta.com/company/careers/'}, {'company': 'Zscaler', 'hq_or_india_hubs': ['Bengaluru', 'Pune'], 'category': 'Global Security', 'ats_type': 'greenhouse', 'slug': 'zscaler', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/zscaler/jobs?content=true', 'careers_page': 'https://www.zscaler.com/careers'}, {'company': 'Figma', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Design/Product', 'ats_type': 'greenhouse', 'slug': 'figma', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/figma/jobs?content=true', 'careers_page': 'https://www.figma.com/careers/'}, {'company': 'Vercel', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevTools', 'ats_type': 'greenhouse', 'slug': 'vercel', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/vercel/jobs?content=true', 'careers_page': 'https://vercel.com/careers'}, {'company': 'Anthropic', 'hq_or_india_hubs': ['Bengaluru', 'Remote-India'], 'category': 'Global AI', 'ats_type': 'greenhouse', 'slug': 'anthropic', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/anthropic/jobs?content=true', 'careers_page': 'https://www.anthropic.com/careers'}, {'company': 'Scale AI', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI', 'ats_type': 'greenhouse', 'slug': 'scaleai', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/scaleai/jobs?content=true', 'careers_page': 'https://scale.com/careers'}, {'company': 'Reddit', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'reddit', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/reddit/jobs?content=true', 'careers_page': 'https://redditinc.com/careers'}, {'company': 'Robinhood', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global Fintech', 'ats_type': 'greenhouse', 'slug': 'robinhood', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/robinhood/jobs?content=true', 'careers_page': 'https://careers.robinhood.com/'}, {'company': 'Notion', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'ashby', 'slug': 'notion', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/notion?includeCompensation=true', 'careers_page': 'https://www.notion.com/careers'}, {'company': 'Linear', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'ashby', 'slug': 'linear', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/linear?includeCompensation=true', 'careers_page': 'https://linear.app/careers'}, {'company': 'Supabase', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevTools', 'ats_type': 'ashby', 'slug': 'supabase', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/supabase?includeCompensation=true', 'careers_page': 'https://supabase.com/careers'}, {'company': 'OpenAI', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI', 'ats_type': 'ashby', 'slug': 'openai', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/openai?includeCompensation=true', 'careers_page': 'https://openai.com/careers/'}, {'company': 'InMobi', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Indian Unicorn', 'ats_type': 'greenhouse', 'slug': 'inmobi', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/inmobi/jobs?content=true', 'careers_page': 'https://www.inmobi.com/company/careers'}, {'company': 'Datadog', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Observability', 'ats_type': 'greenhouse', 'slug': 'datadog', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/datadog/jobs?content=true', 'careers_page': 'https://careers.datadoghq.com/'}, {'company': 'Pinterest', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'pinterest', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/pinterest/jobs?content=true', 'careers_page': 'https://www.pinterestcareers.com/'}, {'company': 'Dropbox', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'dropbox', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/dropbox/jobs?content=true', 'careers_page': 'https://jobs.dropbox.com/'}, {'company': 'Lyft', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'lyft', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/lyft/jobs?content=true', 'careers_page': 'https://www.lyft.com/careers'}, {'company': 'Asana', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global SaaS', 'ats_type': 'greenhouse', 'slug': 'asana', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/asana/jobs?content=true', 'careers_page': 'https://asana.com/jobs'}, {'company': 'PagerDuty', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevOps', 'ats_type': 'greenhouse', 'slug': 'pagerduty', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/pagerduty/jobs?content=true', 'careers_page': 'https://www.pagerduty.com/careers/'}, {'company': 'Fivetran', 'hq_or_india_hubs': ['Bengaluru', 'Remote-India'], 'category': 'Global Data', 'ats_type': 'greenhouse', 'slug': 'fivetran', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/fivetran/jobs?content=true', 'careers_page': 'https://www.fivetran.com/careers'}, {'company': 'Samsara', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global IoT', 'ats_type': 'greenhouse', 'slug': 'samsara', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/samsara/jobs?content=true', 'careers_page': 'https://www.samsara.com/company/careers'}, {'company': 'Discord', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'discord', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/discord/jobs?content=true', 'careers_page': 'https://discord.com/careers'}, {'company': 'Duolingo', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'duolingo', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/duolingo/jobs?content=true', 'careers_page': 'https://careers.duolingo.com/'}, {'company': 'Airtable', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global SaaS', 'ats_type': 'greenhouse', 'slug': 'airtable', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/airtable/jobs?content=true', 'careers_page': 'https://airtable.com/careers'}, {'company': 'Grammarly', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI Product', 'ats_type': 'greenhouse', 'slug': 'grammarly', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/grammarly/jobs?content=true', 'careers_page': 'https://www.grammarly.com/jobs'}, {'company': 'Intercom', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global SaaS', 'ats_type': 'greenhouse', 'slug': 'intercom', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/intercom/jobs?content=true', 'careers_page': 'https://www.intercom.com/careers'}, {'company': 'Glean', 'hq_or_india_hubs': ['Bengaluru'], 'category': 'Global AI', 'ats_type': 'greenhouse', 'slug': 'gleanwork', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/gleanwork/jobs?content=true', 'careers_page': 'https://www.glean.com/careers'}, {'company': 'Instacart', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'greenhouse', 'slug': 'instacart', 'fetch_method': 'http_get_json', 'api_url': 'https://boards-api.greenhouse.io/v1/boards/instacart/jobs?content=true', 'careers_page': 'https://careers.instacart.com/'}, {'company': 'Plaid', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Fintech', 'ats_type': 'lever', 'slug': 'plaid', 'fetch_method': 'http_get_json', 'api_url': 'https://api.lever.co/v0/postings/plaid?mode=json', 'careers_page': 'https://plaid.com/careers/'}, {'company': 'Palantir', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Data/AI', 'ats_type': 'lever', 'slug': 'palantir', 'fetch_method': 'http_get_json', 'api_url': 'https://api.lever.co/v0/postings/palantir?mode=json', 'careers_page': 'https://www.palantir.com/careers/'}, {'company': 'Spotify', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Product', 'ats_type': 'lever', 'slug': 'spotify', 'fetch_method': 'http_get_json', 'api_url': 'https://api.lever.co/v0/postings/spotify?mode=json', 'careers_page': 'https://www.lifeatspotify.com/jobs'}, {'company': 'Ramp', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global Fintech', 'ats_type': 'ashby', 'slug': 'ramp', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/ramp?includeCompensation=true', 'careers_page': 'https://ramp.com/careers'}, {'company': 'Deel', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global HR Tech', 'ats_type': 'ashby', 'slug': 'deel', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/deel?includeCompensation=true', 'careers_page': 'https://www.deel.com/careers/'}, {'company': 'Perplexity', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI', 'ats_type': 'ashby', 'slug': 'perplexity', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/perplexity?includeCompensation=true', 'careers_page': 'https://www.perplexity.ai/hub/careers'}, {'company': 'Replit', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevTools', 'ats_type': 'ashby', 'slug': 'replit', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/replit?includeCompensation=true', 'careers_page': 'https://replit.com/careers'}, {'company': 'Retool', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global DevTools', 'ats_type': 'ashby', 'slug': 'retool', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/retool?includeCompensation=true', 'careers_page': 'https://retool.com/careers'}, {'company': 'Zapier', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global SaaS', 'ats_type': 'ashby', 'slug': 'zapier', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/zapier?includeCompensation=true', 'careers_page': 'https://zapier.com/jobs'}, {'company': 'Cohere', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI', 'ats_type': 'ashby', 'slug': 'cohere', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/cohere?includeCompensation=true', 'careers_page': 'https://cohere.com/careers'}, {'company': 'ElevenLabs', 'hq_or_india_hubs': ['Remote-India'], 'category': 'Global AI', 'ats_type': 'ashby', 'slug': 'elevenlabs', 'fetch_method': 'http_get_json', 'api_url': 'https://api.ashbyhq.com/posting-api/job-board/elevenlabs?includeCompensation=true', 'careers_page': 'https://elevenlabs.io/careers'}, {'company': 'NVIDIA', 'hq_or_india_hubs': ['Bengaluru', 'Hyderabad', 'Pune'], 'category': 'Global Semiconductor/AI', 'ats_type': 'workday', 'slug': 'nvidia', 'fetch_method': 'http_post_json', 'api_url': 'https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs', 'careers_page': 'https://www.nvidia.com/en-in/about-nvidia/careers/'}, {'company': 'Adobe', 'hq_or_india_hubs': ['Bengaluru', 'Noida'], 'category': 'Global Big Tech', 'ats_type': 'workday', 'slug': 'adobe', 'fetch_method': 'http_post_json', 'api_url': 'https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs', 'careers_page': 'https://careers.adobe.com/'}, {'company': 'Salesforce', 'hq_or_india_hubs': ['Hyderabad', 'Bengaluru'], 'category': 'Global SaaS', 'ats_type': 'workday', 'slug': 'salesforce', 'fetch_method': 'http_post_json', 'api_url': 'https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs', 'careers_page': 'https://careers.salesforce.com/'}, {'company': 'Walmart Global Tech', 'hq_or_india_hubs': ['Bengaluru', 'Chennai'], 'category': 'Global Retail Tech', 'ats_type': 'workday', 'slug': 'walmart', 'fetch_method': 'http_post_json', 'api_url': 'https://walmart.wd5.myworkdayjobs.com/wday/cxs/walmart/WalmartExternal/jobs', 'careers_page': 'https://careers.walmart.com/'}, {'company': 'Mastercard', 'hq_or_india_hubs': ['Pune', 'Gurugram'], 'category': 'Global Fintech', 'ats_type': 'workday', 'slug': 'mastercard', 'fetch_method': 'http_post_json', 'api_url': 'https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs', 'careers_page': 'https://careers.mastercard.com/'}, {'company': 'Intel', 'hq_or_india_hubs': ['Bengaluru', 'Hyderabad'], 'category': 'Global Semiconductor', 'ats_type': 'workday', 'slug': 'intel', 'fetch_method': 'http_post_json', 'api_url': 'https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs', 'careers_page': 'https://jobs.intel.com/'}, {'company': 'Dell Technologies', 'hq_or_india_hubs': ['Bengaluru', 'Hyderabad'], 'category': 'Global Hardware/Software MNC', 'ats_type': 'workday', 'slug': 'dell', 'fetch_method': 'http_post_json', 'api_url': 'https://dell.wd1.myworkdayjobs.com/wday/cxs/dell/External/jobs', 'careers_page': 'https://jobs.dell.com/'}]

CUSTOM_PORTALS = [{'company': 'Zepto', 'host': 'zeptonow.com'}, {'company': 'Meesho', 'host': 'meesho.io'}, {'company': 'Swiggy', 'host': 'careers.swiggy.com'}, {'company': 'Zomato', 'host': 'zomato.com'}, {'company': 'PhonePe', 'host': 'phonepe.com'}, {'company': 'Darwinbox', 'host': 'explore.darwinbox.com'}, {'company': 'Sprinto', 'host': 'sprinto.com'}, {'company': 'Hasura', 'host': 'hasura.io'}, {'company': 'Appsmith', 'host': 'appsmith.com'}, {'company': 'Setu', 'host': 'setu.co'}, {'company': 'Juspay', 'host': 'juspay.in'}, {'company': 'Slice', 'host': 'sliceit.com'}, {'company': 'Jupiter', 'host': 'jupiter.money'}, {'company': 'Chargebee', 'host': 'chargebee.com'}, {'company': 'Freshworks', 'host': 'freshworks.com'}, {'company': 'Zoho', 'host': 'zoho.com'}, {'company': 'Gupshup', 'host': 'gupshup.io'}, {'company': 'Innovaccer', 'host': 'innovaccer.com'}, {'company': 'CleverTap', 'host': 'clevertap.com'}, {'company': 'Hevo Data', 'host': 'hevodata.com'}, {'company': 'Scrut Automation', 'host': 'scrut.io'}, {'company': 'Kissflow', 'host': 'kissflow.com'}, {'company': 'Whatfix', 'host': 'whatfix.com'}, {'company': 'HighRadius', 'host': 'highradius.com'}, {'company': 'Flipkart', 'host': 'flipkartcareers.com'}, {'company': 'Paytm', 'host': 'paytm.com'}, {'company': 'Dream11', 'host': 'dreamsports.group'}, {'company': 'Rapido', 'host': 'rapido.bike'}, {'company': 'Lenskart', 'host': 'lenskart.com'}, {'company': 'Google', 'host': 'google.com'}, {'company': 'Microsoft', 'host': 'careers.microsoft.com'}, {'company': 'Amazon', 'host': 'amazon.jobs'}, {'company': 'Uber', 'host': 'uber.com'}, {'company': 'Atlassian', 'host': 'atlassian.com'}, {'company': 'Snowflake', 'host': 'careers.snowflake.com'}, {'company': 'Confluent', 'host': 'confluent.io'}, {'company': 'Palo Alto Networks', 'host': 'jobs.paloaltonetworks.com'}, {'company': 'Rubrik', 'host': 'rubrik.com'}, {'company': 'Nutanix', 'host': 'nutanix.com'}, {'company': 'Cohesity', 'host': 'cohesity.com'}, {'company': 'CrowdStrike', 'host': 'crowdstrike.com'}, {'company': 'ThoughtSpot', 'host': 'thoughtspot.com'}, {'company': 'Intuit', 'host': 'jobs.intuit.com'}, {'company': 'Khatabook', 'host': 'khatabook.com'}, {'company': 'Unacademy', 'host': 'unacademy.com'}, {'company': 'upGrad', 'host': 'upgrad.com'}, {'company': 'PhysicsWallah', 'host': 'pw.live'}, {'company': 'Delhivery', 'host': 'delhivery.com'}, {'company': 'Nykaa', 'host': 'nykaa.com'}, {'company': 'PolicyBazaar', 'host': 'policybazaar.com'}, {'company': 'Pine Labs', 'host': 'pinelabs.com'}, {'company': 'OYO', 'host': 'oyorooms.com'}, {'company': 'MakeMyTrip', 'host': 'careers.makemytrip.com'}, {'company': 'Ola', 'host': 'olacabs.com'}, {'company': 'Urban Company', 'host': 'careers.urbancompany.com'}, {'company': 'ShareChat', 'host': 'sharechat.com'}, {'company': 'CARS24', 'host': 'cars24.com'}, {'company': 'Spinny', 'host': 'spinny.com'}, {'company': 'Navi', 'host': 'navi.com'}, {'company': 'MobiKwik', 'host': 'mobikwik.com'}, {'company': 'Acko', 'host': 'acko.com'}, {'company': 'Zeta', 'host': 'zeta.tech'}, {'company': 'Zerodha', 'host': 'zerodha.com'}, {'company': 'Cult.fit', 'host': 'cult.fit'}, {'company': 'Sarvam AI', 'host': 'sarvam.ai'}, {'company': 'Fractal Analytics', 'host': 'fractal.ai'}, {'company': 'Tata Consultancy Services', 'host': 'tcs.com'}, {'company': 'Infosys', 'host': 'infosys.com'}, {'company': 'Wipro', 'host': 'careers.wipro.com'}, {'company': 'HCLTech', 'host': 'hcltech.com'}, {'company': 'Tech Mahindra', 'host': 'careers.techmahindra.com'}, {'company': 'LTIMindtree', 'host': 'ltimindtree.com'}, {'company': 'Mphasis', 'host': 'careers.mphasis.com'}, {'company': 'Deloitte', 'host': 'www2.deloitte.com'}, {'company': 'PwC', 'host': 'pwc.in'}, {'company': 'EY', 'host': 'ey.com'}, {'company': 'KPMG', 'host': 'kpmg.com'}, {'company': 'Accenture', 'host': 'accenture.com'}, {'company': 'Capgemini', 'host': 'capgemini.com'}, {'company': 'Cognizant', 'host': 'careers.cognizant.com'}, {'company': 'IBM', 'host': 'ibm.com'}, {'company': 'Netflix', 'host': 'jobs.netflix.com'}, {'company': 'Meta', 'host': 'metacareers.com'}, {'company': 'Apple', 'host': 'jobs.apple.com'}, {'company': 'Oracle', 'host': 'careers.oracle.com'}, {'company': 'SAP', 'host': 'jobs.sap.com'}, {'company': 'Cisco', 'host': 'jobs.cisco.com'}, {'company': 'Goldman Sachs', 'host': 'goldmansachs.com'}, {'company': 'JPMorgan Chase', 'host': 'careers.jpmorgan.com'}, {'company': 'Morgan Stanley', 'host': 'morganstanley.com'}, {'company': 'American Express', 'host': 'americanexpress.com'}, {'company': 'Visa', 'host': 'usa.visa.com'}, {'company': 'PayPal', 'host': 'paypal.eightfold.ai'}, {'company': 'Broadcom (VMware)', 'host': 'broadcom.wd1.myworkdayjobs.com'}]


def _strip_html(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_valid_tech_role(title: str, location: str) -> bool:
    t = title.lower()
    loc = (location or "").lower()

    tech_terms = (
        "software", "engineer", "developer", "sde", "intern", "internship",
        "backend", "frontend", "full stack", "fullstack", "systems", "infrastructure",
        "platform", "data", "ml", "ai", "security", "cloud", "devops", "sre",
        "mobile", "android", "ios", "distributed", "product engineer",
        "new grad", "university", "graduate", "2026", "2027", "mts", "member of technical staff"
    )
    if not any(k in t for k in tech_terms):
        return False

    bad_titles = (
        "director", "vp ", "vice president", "head of", "principal", "distinguished",
        "fellow", "staff ", "manager", "tech lead", "team lead", "architect",
        "wordpress", "shopify", "sales", "recruiter", "account executive", "marketing",
        "senior ", "sr.", "sr ", "iii", "iv", "lead "
    )
    if any(b in t for b in bad_titles):
        return False

    blocked_regions = (
        "united states", "usa", "americas", "latam", "canada", "emea", "europe",
        "uk", "london", "san francisco", "new york", "seattle", "austin", "boston", "berlin", "dublin"
    )
    india_or_global = (
        "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "noida",
        "gurugram", "gurgaon", "chennai", "delhi", "apac", "anywhere"
    )

    if any(r in loc for r in blocked_regions) and not any(i in loc for i in india_or_global):
        return False

    return any(i in loc for i in india_or_global) or loc.strip() in ("remote", "global remote")


async def _fetch_single_board(client: httpx.AsyncClient, sem: asyncio.Semaphore, board: dict) -> list[dict]:
    api_url = board["api_url"]
    ats_type = board["ats_type"]
    company = board["company"]
    category = board.get("category") or "Tech Company"
    careers_page = board.get("careers_page") or ""

    async with sem:
        try:
            if ats_type == "workday":
                resp = await client.post(
                    api_url,
                    json={"limit": 20, "offset": 0, "searchText": "Software"},
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    timeout=12.0,
                )
            else:
                resp = await client.get(api_url, timeout=12.0)
            if resp.status_code != 200:
                return []
            payload = resp.json()
        except Exception:
            return []

    jobs = []
    if ats_type == "greenhouse":
        for item in payload.get("jobs", []):
            title = item.get("title", "")
            loc = (item.get("location") or {}).get("name") or ""
            if not _is_valid_tech_role(title, loc):
                continue
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80] or "Bengaluru, India",
                "platform": f"Greenhouse ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("absolute_url") or careers_page,
                "posted_at": (item.get("updated_at") or "")[:10] or "Active (2026)",
                "salary_range": "",
                "description": _strip_html(item.get("content", ""))[:950],
            })
    elif ats_type == "lever":
        listings = payload if isinstance(payload, list) else payload.get("data", [])
        for item in listings:
            title = item.get("text", "")
            loc = (item.get("categories") or {}).get("location") or "Bengaluru, India"
            if not _is_valid_tech_role(title, loc):
                continue
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80],
                "platform": f"Lever ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("hostedUrl") or item.get("applyUrl") or careers_page,
                "posted_at": "Active (2026)",
                "salary_range": "",
                "description": _strip_html(item.get("descriptionPlain") or item.get("description", ""))[:950],
            })
    elif ats_type == "ashby":
        for item in payload.get("jobs", []):
            title = item.get("title", "")
            loc = item.get("location") or ""
            if not _is_valid_tech_role(title, loc):
                continue
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80] or "India / Remote",
                "platform": f"Ashby ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": item.get("jobUrl") or item.get("applyUrl") or careers_page,
                "posted_at": (item.get("publishedAt") or "")[:10] or "Active (2026)",
                "salary_range": item.get("compensationTierSummary") or "",
                "description": _strip_html(item.get("descriptionPlain") or item.get("descriptionHtml", ""))[:950],
            })
    elif ats_type == "workday":
        base_wd = api_url.split("/wday/")[0]
        for item in payload.get("jobPostings", []):
            title = item.get("title", "")
            loc = item.get("locationsText") or ""
            if not _is_valid_tech_role(title, loc):
                continue
            ext_path = item.get("externalPath") or ""
            apply_link = f"{base_wd}/en-US{ext_path}" if ext_path else careers_page
            jobs.append({
                "title": title[:100],
                "company": company,
                "location": loc[:80] or "Bengaluru / Hyderabad, India",
                "platform": f"Workday ? {category}",
                "source_tier": "Direct ATS",
                "apply_url": apply_link,
                "posted_at": item.get("postedOn") or "Active (2026)",
                "salary_range": "",
                "description": f"{title} at {company} ({loc})",
            })
    return jobs


async def _fetch_all_direct_ats(client: httpx.AsyncClient) -> list[dict]:
    now = time.time()
    if _ATS_CACHE["jobs"] and (now - _ATS_CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        return list(_ATS_CACHE["jobs"])

    sem = asyncio.Semaphore(16)
    nested = await asyncio.gather(*[_fetch_single_board(client, sem, b) for b in DIRECT_BOARDS])
    harvested = [j for group in nested for j in group]
    if harvested:
        _ATS_CACHE["timestamp"] = now
        _ATS_CACHE["jobs"] = harvested
    return harvested


async def _fetch_custom_portals_via_tavily(client: httpx.AsyncClient, flat_skills: list[str]) -> list[dict]:
    if not TAVILY_API_KEY:
        return []

    skills_str = " ".join(flat_skills[:3]) if flat_skills else "Python C++ Backend"
    unique_hosts = list({p["host"]: p["company"] for p in CUSTOM_PORTALS}.items())
    chunk_size = max(1, (len(unique_hosts) + 2) // 3)
    batches = [unique_hosts[i:i + chunk_size] for i in range(0, len(unique_hosts), chunk_size)]

    async def _query(host_pairs: list[tuple[str, str]]) -> list[dict]:
        if not host_pairs:
            return []
        domains = [h for h, _ in host_pairs]
        try:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": f'("Software Engineer" OR "SDE" OR "Intern") {skills_str} India (intern OR 2026 OR 2027 OR SDE-1)',
                    "include_domains": domains,
                    "search_depth": "advanced",
                    "max_results": 7,
                    "days": 30,
                    "include_answer": False,
                },
                timeout=16.0,
            )
            if resp.status_code != 200:
                return []
            out = []
            for item in resp.json().get("results", []):
                url = item.get("url", "")
                title = item.get("title", "").split("|")[0].split(" - ")[0].strip()
                if not url or not title:
                    continue
                if any(bad in title.lower() for bad in ("director", "staff", "principal", "manager", "lead", "senior", "careers at", "jobs at")):
                    continue
                comp = next((c for h, c in host_pairs if h in url.lower()), "Tech Company")
                out.append({
                    "title": title[:95],
                    "company": comp,
                    "location": "Bengaluru / Hyderabad, India",
                    "platform": "Direct Career Portal",
                    "source_tier": "Custom Portal",
                    "apply_url": url,
                    "posted_at": item.get("published_date") or "Active (2026)",
                    "salary_range": "",
                    "description": item.get("content", "")[:900],
                })
            return out
        except Exception:
            return []

    groups = await asyncio.gather(*[_query(b) for b in batches])
    return [j for g in groups for j in g]


def _local_pre_score(job: dict, flat_skills: list[str], target_role: str) -> int:
    text = f"{job.get('title', '')} {job.get('description', '')} {job.get('location', '')}".lower()
    score = 35 if job.get("source_tier") == "Direct ATS" else 22
    for kw in ("intern", "internship", "2026", "2027", "sde-1", "sde 1", "new grad", "university", "graduate", "junior", "associate", "software engineer i", "sde i"):
        if kw in job.get("title", "").lower():
            score += 22
    for loc in ("india", "bengaluru", "bangalore", "hyderabad", "pune", "noida", "gurugram", "chennai", "mumbai"):
        if loc in text:
            score += 15
            break
    for sk in flat_skills[:12]:
        if sk.lower() in text:
            score += 6
    return score


async def _score_jobs_with_groq(user_profile: dict, candidate_jobs: list[dict], flat_skills: list[str]) -> list[dict]:
    if not candidate_jobs:
        return []
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing in environment variables.")

    client = AsyncGroq(api_key=GROQ_API_KEY)
    models_resp = await client.models.list()
    all_ids = [m.id for m in models_resp.data]
    preferred = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    chosen_model = next((m for m in preferred if m in all_ids), all_ids[0])

    compact_jobs = [
        {
            "idx": i,
            "title": j["title"],
            "company": j["company"],
            "location": j["location"],
            "platform": j["platform"],
            "source_tier": j["source_tier"],
            "salary_range": j.get("salary_range", ""),
            "apply_url": j["apply_url"],
            "posted_at": j.get("posted_at", "Active (2026)"),
            "snippet": j["description"][:650],
        }
        for i, j in enumerate(candidate_jobs[:18])
    ]

    prompt = f"""
You are a precision Technical Recruiter & ATS Matching Engine.
Select and score the BEST 12 distinct early-career software engineering / internship roles from these 155 direct company career portals.

CANDIDATE PROFILE:
- Name: {user_profile.get('full_name', 'Candidate')}
- Target Role: {user_profile.get('target_role', 'Software Engineer')}
- Candidate ALREADY KNOWS these skills (NEVER list any of these in missing_skills!): {json.dumps(flat_skills)}
- Resume Summary: {user_profile.get('summary', '')}

DIRECT COMPANY CAREER LISTINGS:
{json.dumps(compact_jobs, indent=2)}

STRICT RULES:
1. Prioritize Internships, 2026/2027 New Grad, SDE-1, and early-career Software Engineer roles in India or Remote-India.
2. NEVER put any skill from `Candidate ALREADY KNOWS` inside `missing_skills`! Only list 1 to 3 genuinely missing job-specific technologies (e.g. Go, Rust, Kubernetes, Kafka, Ruby, Scala) not in the candidate's verified skills list.
3. Preserve exact `company`, `apply_url`, `platform`, and `source_tier` from the input.
4. Set `work_mode` to `"Remote"`, `"Hybrid"`, or `"On-site"`, and `experience_level` to `"Entry"` or `"Mid"`.
5. Compute a realistic `match_score` (75 to 96) and write a crisp `tailored_pitch` (2 sentences referencing the candidate's real skills/projects) + `why_fit`.

Return ONLY raw valid JSON:
{{
  "matched_jobs": [
    {{
      "title": "string",
      "company": "string",
      "location": "string",
      "work_mode": "Hybrid",
      "experience_level": "Entry",
      "platform": "string",
      "source_tier": "Direct ATS",
      "salary_range": "string",
      "posted_at": "string",
      "apply_url": "string",
      "match_score": 91,
      "matched_skills": ["Python", "C++"],
      "missing_skills": ["Go", "Kubernetes"],
      "why_fit": "string",
      "tailored_pitch": "string"
    }}
  ]
}}
"""

    completion = await client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": "You are a precision ATS JSON API. Output ONLY raw valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.15,
        max_tokens=4096,
    )

    parsed = json.loads(completion.choices[0].message.content)
    jobs = parsed.get("matched_jobs", [])
    known_lower = {s.lower() for s in flat_skills}
    for j in jobs:
        j["match_percentage"] = j.get("match_score", 82)
        j["missing_skills"] = [s for s in (j.get("missing_skills") or []) if s.lower() not in known_lower][:4]
    jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return jobs


async def find_and_score_jobs(user_profile: dict) -> list[dict]:
    raw_skills = user_profile.get("verified_skills", [])
    if isinstance(raw_skills, dict):
        flat_skills = [s for v in raw_skills.values() if isinstance(v, list) for s in v]
    else:
        flat_skills = list(raw_skills)

    target_role = user_profile.get("target_role") or "Software Engineer"

    async with httpx.AsyncClient(headers={"User-Agent": "WingStack-ATS-Scout/3.0"}) as http_client:
        ats_jobs, custom_jobs = await asyncio.gather(
            _fetch_all_direct_ats(http_client),
            _fetch_custom_portals_via_tavily(http_client, flat_skills),
        )

    seen_keys = set()
    deduped = []
    for job in ats_jobs + custom_jobs:
        url = (job.get("apply_url") or "").strip()
        key = (job.get("company", "").lower(), job.get("title", "").lower(), url)
        if url and key not in seen_keys:
            seen_keys.add(key)
            job["_pre_score"] = _local_pre_score(job, flat_skills, target_role)
            deduped.append(job)

    deduped.sort(key=lambda x: x.get("_pre_score", 0), reverse=True)
    return await _score_jobs_with_groq(user_profile, deduped[:18], flat_skills)
