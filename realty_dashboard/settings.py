from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['*']

# TATA API Configuration
TATA_AUTH_TOKEN = os.getenv('TATA_AUTH_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaG9uZU51bWJlciI6Iis5MTkzNTU0MjE2MTYiLCJwaG9uZU51bWJlcklkIjoiMTAwNTUxNjc5NzU0ODg3IiwiaWF0IjoxNjg2OTA5MDMzfQ.39dmKyOC6dSv83jdtw4dezjpX6NnLkdHueZHenVybkc')
TATA_BASE_URL = os.getenv('TATA_BASE_URL', 'https://wb.omni.tatatelebusiness.com')

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER = os.getenv('WHATSAPP_PHONE_NUMBER', '+919355421616')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '100551679754887')
WABA_ID = os.getenv('WABA_ID', '101005859708868')
FACEBOOK_BUSINESS_MANAGER_ID = os.getenv('FACEBOOK_BUSINESS_MANAGER_ID', '247009066912067')
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN', 'bop_realty_webhook_verify_2024')

# Integration IDs
CRM_API_INTEGRATION_ID = os.getenv('CRM_API_INTEGRATION_ID', '688c9bda7a8e4dcedd266675')
WHATSAPP_OPENAI_BOT_ID = os.getenv('WHATSAPP_OPENAI_BOT_ID', '6889cc1c555a708f04701a1f')
CRM_WEBHOOK_URL = os.getenv('CRM_WEBHOOK_URL', 'https://crm-1z7t.onrender.com/webhook/')

# TATA IVR Configuration
TATA_IVR_TOKEN = os.getenv('TATA_IVR_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwaG9uZU51bWJlciI6Iis5MTkzNTU0MjE2MTYiLCJwaG9uZU51bWJlcklkIjoiMTAwNTUxNjc5NzU0ODg3IiwiaWF0IjoxNjg2OTA5MDMzfQ.39dmKyOC6dSv83jdtw4dezjpX6NnLkdHueZHenVybkc')

# WhatsApp Rate Limiting (100k/24h = ~1.15 msg/sec)
WHATSAPP_RATE_LIMIT_DELAY = float(os.getenv('WHATSAPP_RATE_LIMIT_DELAY', '1.25'))
WHATSAPP_DAILY_LIMIT = int(os.getenv('WHATSAPP_DAILY_LIMIT', '100000')) 


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'realty_dashboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'realty_dashboard.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Database
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
