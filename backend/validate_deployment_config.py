#!/usr/bin/env python3
"""
Validation script for UrbanGuard AI deployment configuration
Checks that all required files and configurations are in place
"""
import os
import sys
import yaml

try:
    import tomli
    HAS_TOMLI = True
except ImportError:
    HAS_TOMLI = False


def check_file_exists(filepath, description):
    """Check if a file exists and print status"""
    if os.path.exists(filepath):
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} MISSING: {filepath}")
        return False


def validate_template_yaml():
    """Validate template.yaml structure"""
    print("\n=== Validating template.yaml ===")
    
    if not check_file_exists("template.yaml", "SAM template"):
        return False
    
    try:
        # Use safe_load with custom constructor for CloudFormation intrinsic functions
        def cfn_constructor(loader, tag_suffix, node):
            """Handle CloudFormation intrinsic functions"""
            if isinstance(node, yaml.ScalarNode):
                return loader.construct_scalar(node)
            elif isinstance(node, yaml.SequenceNode):
                return loader.construct_sequence(node)
            elif isinstance(node, yaml.MappingNode):
                return loader.construct_mapping(node)
            return None
        
        yaml.add_multi_constructor('!', cfn_constructor, Loader=yaml.SafeLoader)
        
        with open("template.yaml", "r") as f:
            template = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ["AWSTemplateFormatVersion", "Transform", "Resources", "Outputs"]
        for section in required_sections:
            if section in template:
                print(f"  ✓ Section '{section}' present")
            else:
                print(f"  ✗ Section '{section}' MISSING")
                return False
        
        # Check Lambda function
        resources = template.get("Resources", {})
        if "UrbanGuardApiFunction" in resources:
            print("  ✓ Lambda function defined")
            func = resources["UrbanGuardApiFunction"]
            if func.get("Type") == "AWS::Serverless::Function":
                print("    ✓ Correct resource type")
            if "Handler" in func.get("Properties", {}):
                handler = func["Properties"]["Handler"]
                print(f"    ✓ Handler: {handler}")
        else:
            print("  ✗ Lambda function NOT defined")
            return False
        
        # Check API Gateway
        if "UrbanGuardApi" in resources:
            print("  ✓ API Gateway defined")
        else:
            print("  ✗ API Gateway NOT defined")
            return False
        
        # Check DynamoDB tables
        tables = ["ComplaintsTable", "RiskZonesTable", "DailyReportsTable"]
        for table in tables:
            if table in resources:
                print(f"  ✓ DynamoDB table '{table}' defined")
            else:
                print(f"  ✗ DynamoDB table '{table}' NOT defined")
                return False
        
        # Check CloudWatch log groups
        log_groups = ["UrbanGuardLogGroup", "ApiGatewayLogGroup"]
        for log_group in log_groups:
            if log_group in resources:
                print(f"  ✓ CloudWatch log group '{log_group}' defined")
            else:
                print(f"  ✗ CloudWatch log group '{log_group}' NOT defined")
                return False
        
        # Check outputs
        outputs = template.get("Outputs", {})
        required_outputs = ["ApiUrl", "LambdaFunctionArn", "ComplaintsTableName"]
        for output in required_outputs:
            if output in outputs:
                print(f"  ✓ Output '{output}' defined")
            else:
                print(f"  ✗ Output '{output}' NOT defined")
                return False
        
        print("✓ template.yaml validation PASSED")
        return True
        
    except yaml.YAMLError as e:
        print(f"✗ YAML parsing error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_samconfig_toml():
    """Validate samconfig.toml structure"""
    print("\n=== Validating samconfig.toml ===")
    
    if not check_file_exists("samconfig.toml", "SAM config"):
        return False
    
    if not HAS_TOMLI:
        print("  ⚠ tomli module not installed, skipping detailed validation")
        print("  ✓ File exists (basic check)")
        return True
    
    try:
        with open("samconfig.toml", "rb") as f:
            config = tomli.load(f)
        
        # Check environments
        environments = ["default", "prod", "staging"]
        for env in environments:
            if env in config:
                print(f"  ✓ Environment '{env}' configured")
            else:
                print(f"  ✗ Environment '{env}' NOT configured")
                return False
        
        print("✓ samconfig.toml validation PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_documentation():
    """Validate documentation files"""
    print("\n=== Validating Documentation ===")
    
    docs = [
        ("DEPLOYMENT_GUIDE.md", "Deployment guide"),
        ("DEPLOYMENT_QUICK_START.md", "Quick start guide"),
        ("AWS_LAMBDA_SETUP.md", "Lambda setup guide"),
    ]
    
    all_present = True
    for filepath, description in docs:
        if not check_file_exists(filepath, description):
            all_present = False
    
    if all_present:
        print("✓ Documentation validation PASSED")
    return all_present


def validate_lambda_handler():
    """Validate Lambda handler file"""
    print("\n=== Validating Lambda Handler ===")
    
    if not check_file_exists("lambda_handler.py", "Lambda handler"):
        return False
    
    try:
        with open("lambda_handler.py", "r") as f:
            content = f.read()
        
        # Check for required imports and functions
        required_elements = [
            ("from mangum import Mangum", "Mangum import"),
            ("from main import app", "FastAPI app import"),
            ("def lambda_handler(event, context)", "Lambda handler function"),
        ]
        
        for element, description in required_elements:
            if element in content:
                print(f"  ✓ {description} present")
            else:
                print(f"  ✗ {description} MISSING")
                return False
        
        print("✓ Lambda handler validation PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def validate_dependencies():
    """Validate requirements.txt has necessary dependencies"""
    print("\n=== Validating Dependencies ===")
    
    if not check_file_exists("requirements.txt", "Requirements file"):
        return False
    
    try:
        with open("requirements.txt", "r") as f:
            requirements = f.read()
        
        required_packages = [
            ("fastapi", "FastAPI"),
            ("mangum", "Mangum (Lambda adapter)"),
            ("boto3", "Boto3 (AWS SDK)"),
            ("pydantic", "Pydantic"),
        ]
        
        for package, description in required_packages:
            if package in requirements:
                print(f"  ✓ {description} present")
            else:
                print(f"  ✗ {description} MISSING")
                return False
        
        print("✓ Dependencies validation PASSED")
        return True
        
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False


def main():
    """Run all validations"""
    print("=" * 70)
    print("UrbanGuard AI - Deployment Configuration Validation")
    print("=" * 70)
    
    validations = [
        validate_template_yaml,
        validate_samconfig_toml,
        validate_documentation,
        validate_lambda_handler,
        validate_dependencies,
    ]
    
    results = [validation() for validation in validations]
    
    print("\n" + "=" * 70)
    if all(results):
        print("✓ ALL VALIDATIONS PASSED")
        print("=" * 70)
        print("\nDeployment configuration is ready!")
        print("\nNext steps:")
        print("  1. Install AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html")
        print("  2. Configure AWS credentials: aws configure")
        print("  3. Build and deploy: sam build && sam deploy --guided")
        print("\nSee DEPLOYMENT_GUIDE.md for detailed instructions.")
        return 0
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("=" * 70)
        print("\nPlease fix the issues above before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
