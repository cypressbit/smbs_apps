# Scalable Modular Backend System (SMBS)

Welcome to SMBS, an open-source collection of Django-based applications designed to accelerate the development of websites and backend applications. SMBS (Scalable Modular Backend System) has been in development for over three years and is now a mature, stable platform. This suite includes various powerful applications, such as a WYSIWYG blog, full CMS support, a user forum, and an inventory app. Leveraging the full customization power of Python and the stability of Django, SMBS provides a robust foundation for rapid development and deployment.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- **WYSIWYG Blog Application**: Easy-to-use blog platform with rich text editing capabilities.
- **CMS Support**: Create and manage pages with a flexible content management system.
- **User Forum**: A complete forum for user interactions and discussions.
- **Inventory App**: Manage and track inventory efficiently.
- **Modular Design**: Each app is designed to be independent and can be integrated as needed.

## Installation

To get started with SMBS, follow these steps:

1. **Set up your Django project**:

    ```bash
    Copy code
    django-admin startproject website
    cd website
    ```

2. **Clone the repository**:

     ```bash
     git clone https://github.com/cypressbit/smbs_apps.git
     cd smbs_apps
     ```

3. **Configure settings.py**:

    Add the SMBS apps to your INSTALLED_APPS list in settings.py:

    ```python
    INSTALLED_APPS = [
      'django.contrib.admin',
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',
      'smbs_apps.smbs_base',
      'smbs_apps.smbs_blog',
      'smbs_apps.smbs_cities_light',
      'smbs_apps.smbs_alerts',
      'smbs_apps.smbs_comments_tree',
      'smbs_apps.smbs_accounts',
      'smbs_apps.smbs_social',
      'smbs_apps.smbs_reactions',
      'smbs_apps.smbs_pages',
      'smbs_apps.smbs_inventory',
      'smbs_apps.smbs_cart',
      'smbs_apps.smbs_forms',
    ]

4. **Add context processors**:

    Ensure the TEMPLATES setting in settings.py includes the necessary context processors:

    ```python
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'smbs_apps.smbs_base.context_processors.base',
                    'smbs_apps.smbs_pages.context_processors.get_pages',
                    'smbs_apps.smbs_inventory.context_processors.inventory',
                ],
            },
        },
    ]

5. **Run migrations**:

    ```bash
    python manage.py migrate

6. **Create a superuser**:

    ```bash
    python manage.py createsuperuser

7. **Run the development server**:

    ```bash
    python manage.py runserver
    
## Usage

### Project Structure

A typical project structure using SMBS looks like this:

    ```
    ├── smbs_apps
    │   ├── smbs_accounts
    │   ├── smbs_alerts
    │   ├── smbs_base
    │   ├── smbs_blog
    │   ├── smbs_cart
    │   ├── smbs_cities_light
    │   ├── smbs_comments_tree
    │   ├── smbs_contact
    │   ├── smbs_forms
    │   ├── smbs_inventory
    │   ├── smbs_newsletter
    │   ├── smbs_pages
    │   ├── smbs_profile
    │   ├── smbs_qa
    │   ├── smbs_reactions
    │   ├── smbs_social
    │   └── smbs_user_posts
    └── website
        ├── __init__.py
        ├── settings.py
        ├── urls.py
        └── wsgi.py

### Customizing Templates

To override templates, create a templates directory in your project root and add your custom templates there. Ensure the DIRS setting in TEMPLATES points to this directory.

### Contributing
We welcome contributions from the community. To contribute:

- Fork the repository.
- Create a new branch for your feature or bug fix.
- Commit your changes and push to your fork.
- Create a pull request detailing your changes.
- Please ensure your code adheres to the project's coding standards and includes tests where applicable.

## License
SMBS is released under the MIT License. See LICENSE for more information.
