
# Pulumi, Azure, and Django Cookiecutter Template

This is a **Cookiecutter** template for setting up projects with **Pulumi** for infrastructure as code, **Azure** for cloud deployment, and **Django** as the web framework. It provides a structured starting point to automate and standardize project initialization, making it easy to spin up new projects with the same configuration and best practices.

## Features

- **Pulumi Integration**: Automatically sets up infrastructure as code for Azure cloud services using Pulumi.
- **Azure Configuration**: Templates for deploying applications to Azure App Service, storage accounts, and more.
- **Django Project Setup**: Initializes a Django web application with standard configurations.
- **GitHub Actions CI/CD**: Pre-configured workflows for continuous integration and deployment to Azure using GitHub Actions.
- **Environment Management**: Handles environment variable setup for seamless cloud deployment.

## Requirements

- **Cookiecutter**: Install Cookiecutter if you don't have it already:
  ```bash
  pip install cookiecutter
  ```

- **Pulumi**: Install Pulumi CLI.
- **Azure CLI**: Ensure Azure CLI is installed and logged in to your account.
- **Django**: This template assumes familiarity with Django.

## Usage

To generate a new project using this template, run the following command:

```bash
cookiecutter https://github.com/your-username/pulumi-azure-django-cookiecutter.git
```

### Prompts
You'll be prompted to provide the following values:
- `project_name`: The name of your new project.
- `azure_subscription_id`: Your Azure Subscription ID.
- `pulumi_stack`: The Pulumi stack name for managing environments.
- `django_app_name`: The name of the Django app.
- Other optional variables such as database configuration, deployment regions, etc.

## Directory Structure

The template generates the following structure:

```
{{cookiecutter.project_name}}/
├── pulumi/
│   └── Pulumi.yaml
├── django/
│   └── manage.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── README.md
├── requirements.txt
└── .env.example
```

## Contributing

Feel free to submit pull requests or open issues to improve the template. Contributions are always welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
