"""
Configuration settings for livestock data loader
"""
import os

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
PROJECT_NAME = os.getenv('PROJECT_NAME', 'ai-livestock-matching')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

# Table Names (will be updated after Terraform deployment)
# Default names - update these after running Terraform
PRODUCTS_TABLE_NAME = os.getenv('PRODUCTS_TABLE_NAME', f"{PROJECT_NAME}-{ENVIRONMENT}-products")
SELLERS_TABLE_NAME = os.getenv('SELLERS_TABLE_NAME', f"{PROJECT_NAME}-{ENVIRONMENT}-sellers")

# Data File Paths
DATASETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'datasets')
SELLERS_EXCEL_FILE = os.path.join(DATASETS_DIR, 'sellers_dataset.xlsx')

# Verify file exists
if not os.path.exists(SELLERS_EXCEL_FILE):
    print(f"Warning: Excel file not found at {SELLERS_EXCEL_FILE}")
    print("Please ensure the sellers_dataset.xlsx file is in the datasets directory")