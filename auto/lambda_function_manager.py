#!/usr/bin/env python3
"""
AWS Lambda Function Manager
A tool to list and manage AWS Lambda functions
"""

import json
import os
import boto3
from typing import List, Dict, Any, Optional
from pathlib import Path
import argparse


class LambdaFunctionManager:
    """Manager class for AWS Lambda functions - lists, downloads, and uploads Lambda functions"""
    def __init__(self, debug=False):
        self.download_dir = Path('./lambda_downloads')
        self.download_dir.mkdir(exist_ok=True)
        self.clients = {}
        self.debug = debug
    
    
    
    def get_lambda_client(self, region: str):
        """Get or create AWS Lambda client for the specified region"""
        if region not in self.clients:
            self.clients[region] = boto3.client('lambda', region_name=region)
        return self.clients[region]
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def list_lambda_functions(self, region: str) -> List[Dict[str, Any]]:
        """List all Lambda functions in the specified region
        
        Args:
            region: AWS region
        """
        functions = []
        
        try:
            lambda_client = self.get_lambda_client(region)
            
            self._debug_print(f"Listing all Lambda functions in region {region}")
            
            # Get all Lambda functions in the region
            response = lambda_client.list_functions()
            
            for function in response['Functions']:
                try:
                    # Get additional function details
                    function_response = lambda_client.get_function(FunctionName=function['FunctionName'])
                    
                    # Get version information
                    version_info = self._get_version_info(lambda_client, function['FunctionName'])
                    
                    functions.append({
                        'name': function['FunctionName'],
                        'arn': function['FunctionArn'],
                        'description': function.get('Description', ''),
                        'runtime': function['Runtime'],
                        'region': region,
                        'handler': function['Handler'],
                        'code_location': function_response['Code'].get('Location', 'N/A'),
                        'last_modified': function.get('LastModified', ''),
                        'code_size': function.get('CodeSize', 0),
                        'timeout': function.get('Timeout', 0),
                        'memory_size': function.get('MemorySize', 0),
                        'version': function_response['Configuration'].get('Version', '$LATEST'),
                        'code_sha256': function_response['Configuration'].get('CodeSha256', 'N/A'),
                        'versions_available': version_info
                    })
                    self._debug_print(f"Added Lambda function: {function['FunctionName']} (Version: {function_response['Configuration'].get('Version', '$LATEST')})")
                except Exception as e:
                    self._debug_print(f"Error getting details for Lambda function {function['FunctionName']}: {e}")
                    # Still add basic info even if we can't get full details
                    functions.append({
                        'name': function['FunctionName'],
                        'arn': function['FunctionArn'],
                        'description': function.get('Description', ''),
                        'runtime': function['Runtime'],
                        'region': region,
                        'handler': function['Handler'],
                        'code_location': 'N/A',
                        'last_modified': function.get('LastModified', ''),
                        'code_size': function.get('CodeSize', 0),
                        'timeout': function.get('Timeout', 0),
                        'memory_size': function.get('MemorySize', 0),
                        'version': '$LATEST',
                        'code_sha256': 'N/A',
                        'versions_available': []
                    })
                
        except Exception as e:
            print(f"Error listing Lambda functions: {e}")
            if self.debug:
                import traceback
                traceback.print_exc()
        
        self._debug_print(f"Total Lambda functions found: {len(functions)}")
        return functions
    
    def _get_version_info(self, lambda_client, function_name: str) -> List[Dict[str, Any]]:
        """Get available versions for a Lambda function"""
        try:
            response = lambda_client.list_versions_by_function(FunctionName=function_name)
            versions = []
            for version in response.get('Versions', []):
                versions.append({
                    'version': version.get('Version', 'N/A'),
                    'last_modified': version.get('LastModified', 'N/A'),
                    'code_sha256': version.get('CodeSha256', 'N/A'),
                    'description': version.get('Description', '')
                })
            return versions
        except Exception as e:
            self._debug_print(f"Error getting versions for {function_name}: {e}")
            return []
    
    def display_lambda_summary(self, functions: List[Dict[str, Any]]):
        """Display a summary of Lambda functions"""
        if not functions:
            print("No Lambda functions found in this region.")
            return
            
        print(f"\n{'='*60}")
        print("LAMBDA FUNCTIONS SUMMARY")
        print(f"{'='*60}")
        print(f"Found {len(functions)} Lambda functions in the region")
        print("-" * 60)
        
        for func in functions:
            self._display_function_details(func)
        
        print(f"\n{'='*60}")
    
    def _display_function_details(self, func: Dict[str, Any]):
        """Display details for a single Lambda function"""
        print(f"\n📋 Function: {func['name']}")
        print(f"   Runtime: {func['runtime']}")
        print(f"   Handler: {func['handler']}")
        print(f"   Description: {func.get('description', 'No description')}")
        print(f"   Memory: {func.get('memory_size', 'N/A')} MB")
        print(f"   Timeout: {func.get('timeout', 'N/A')} seconds")
        print(f"   Code Size: {func.get('code_size', 'N/A')} bytes")
        print(f"   Version: {func.get('version', '$LATEST')}")
        print(f"   Code SHA256: {func.get('code_sha256', 'N/A')[:16]}...")
        if func.get('last_modified'):
            print(f"   Last Modified: {func['last_modified']}")
        
        # Show available versions
        versions = func.get('versions_available', [])
        if len(versions) > 1:  # More than just $LATEST
            print(f"   Available Versions: {len(versions)} total")
            for v in versions[-3:]:  # Show last 3 versions
                print(f"     - v{v['version']}: {v['last_modified']}")
    
    def download_lambda_code(self, component: Dict[str, Any], type_dir: Path, version: str = None) -> Dict[str, Any]:
        """Download Lambda function source code from S3"""
        import zipfile
        import tempfile
        import os
        import requests
        from urllib.parse import urlparse
        
        try:
            lambda_client = self.get_lambda_client(component['region'])
            
            # Get the function code location (optionally for a specific version)
            function_name = component['arn']
            if version:
                self._debug_print(f"Requesting specific version: {version}")
                response = lambda_client.get_function(
                    FunctionName=function_name,
                    Qualifier=version
                )
            else:
                self._debug_print(f"Requesting $LATEST version")
                response = lambda_client.get_function(
                    FunctionName=function_name
                )
            
            code_location = response['Code'].get('Location')
            function_version = response['Configuration'].get('Version', '$LATEST')
            code_sha256 = response['Configuration'].get('CodeSha256', 'N/A')
            
            if not code_location:
                return {
                    'code_extracted': False,
                    'reason': 'No S3 code location available'
                }
            
            self._debug_print(f"Function Version: {function_version}")
            self._debug_print(f"Code SHA256: {code_sha256}")
            self._debug_print(f"Code location URL: {code_location}")
            
            # Create a subdirectory for the function code
            code_dir = type_dir / f"{component['name']}_code"
            code_dir.mkdir(exist_ok=True)
            
            # Try to parse S3 location for direct S3 download, otherwise use presigned URL
            parsed_url = urlparse(code_location)
            
            if parsed_url.hostname and 's3' in parsed_url.hostname:
                # This is an S3 URL - download directly from S3
                self._debug_print(f"Downloading from S3 URL: {code_location}")
                success = self._download_from_s3_url(code_location, code_dir, component['region'])
            else:
                # Use presigned URL method
                self._debug_print(f"Downloading from presigned URL: {code_location}")
                success = self._download_from_presigned_url(code_location, code_dir)
            
            if success:
                files_extracted = os.listdir(code_dir)
                print(f"Lambda code extracted to: {code_dir}")
                print(f"Version: {function_version}")
                print(f"Code SHA256: {code_sha256}")
                print(f"Files extracted: {files_extracted}")
                
                return {
                    'code_extracted': True,
                    'code_directory': str(code_dir),
                    'files_extracted': files_extracted,
                    'source_location': code_location,
                    'version': function_version,
                    'code_sha256': code_sha256
                }
            else:
                return {
                    'code_extracted': False,
                    'reason': 'Failed to download and extract code'
                }
                
        except Exception as e:
            print(f"Error downloading Lambda code: {e}")
            return {
                'code_extracted': False,
                'reason': str(e)
            }
    
    def _download_from_s3_url(self, s3_url: str, code_dir: Path, region: str) -> bool:
        """Download Lambda code directly from S3 using boto3"""
        import zipfile
        import tempfile
        import os
        from urllib.parse import urlparse
        
        try:
            # Parse S3 URL to extract bucket and key
            parsed_url = urlparse(s3_url)
            
            # Handle different S3 URL formats
            if parsed_url.hostname.startswith('s3'):
                # Format: https://s3.region.amazonaws.com/bucket/key
                path_parts = parsed_url.path.lstrip('/').split('/', 1)
                if len(path_parts) == 2:
                    bucket_name, object_key = path_parts
                else:
                    # Fall back to presigned URL method
                    return self._download_from_presigned_url(s3_url, code_dir)
            elif '.s3.' in parsed_url.hostname or '.s3-' in parsed_url.hostname:
                # Format: https://bucket.s3.region.amazonaws.com/key
                bucket_name = parsed_url.hostname.split('.')[0]
                object_key = parsed_url.path.lstrip('/')
            else:
                # Unknown format, fall back to presigned URL
                return self._download_from_presigned_url(s3_url, code_dir)
            
            self._debug_print(f"S3 Bucket: {bucket_name}, Key: {object_key}")
            
            # Get S3 client
            s3_client = boto3.client('s3', region_name=region)
            
            # Download the zip file from S3
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
                s3_client.download_file(bucket_name, object_key, temp_zip_path)
            
            try:
                # Extract the zip file
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(code_dir)
                return True
            finally:
                os.unlink(temp_zip_path)
                
        except Exception as e:
            self._debug_print(f"S3 download failed: {e}, falling back to presigned URL")
            return self._download_from_presigned_url(s3_url, code_dir)
    
    def _download_from_presigned_url(self, url: str, code_dir: Path) -> bool:
        """Download Lambda code using presigned URL"""
        import zipfile
        import tempfile
        import os
        import requests
        
        try:
            # Download the zip file using requests
            zip_response = requests.get(url, timeout=300)  # 5 minute timeout
            zip_response.raise_for_status()
            
            # Save and extract the zip file
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip.write(zip_response.content)
                temp_zip_path = temp_zip.name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(code_dir)
                return True
            finally:
                os.unlink(temp_zip_path)
                
        except Exception as e:
            print(f"Failed to download from presigned URL: {e}")
            return False
    
    def download_lambda_function(self, component: Dict[str, Any]) -> Optional[str]:
        """Download Lambda function source code"""
        name = component['name']
        region = component['region']
        
        # Create directory structure
        region_dir = self.download_dir / region
        type_dir = region_dir / 'lambda_functions'
        type_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download source code only
            code_content = self.download_lambda_code(component, type_dir)
            
            if code_content.get('code_extracted'):
                code_dir = code_content['code_directory']
                print(f"Downloaded Lambda function code: {name} to {code_dir}")
                return code_dir
            else:
                print(f"Failed to download Lambda function code: {code_content.get('reason', 'Unknown error')}")
                return None
            
        except Exception as e:
            print(f"Error downloading Lambda function: {e}")
            return None
    
    def _clean_lambda_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Clean Lambda response for editing"""
        function_config = response['Configuration']
        keys_to_keep = [
            'FunctionName', 'Description', 'Runtime', 'Handler', 'Environment',
            'Timeout', 'MemorySize', 'DeadLetterConfig', 'TracingConfig'
        ]
        return {k: v for k, v in function_config.items() if k in keys_to_keep}
    
    def upload_lambda_function(self, file_path: str, region: str = None) -> bool:
        """Upload Lambda function configuration and code"""
        try:
            with open(file_path, 'r') as f:
                content = json.load(f)
            
            # If region not provided, try to determine from content or use default
            if not region:
                region = content.get('region', 'us-east-1')
            
            lambda_client = self.get_lambda_client(region)
            
            if 'configuration' in content:
                config = content['configuration']
                function_name = config['FunctionName']
                
                # Update function configuration
                response = lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    **{k: v for k, v in config.items() if k != 'FunctionName'}
                )
                print(f"Successfully updated Lambda function configuration: {function_name}")
                
                # Check if there's code to upload
                if 'code_info' in content and content['code_info'].get('code_directory'):
                    code_dir = content['code_info']['code_directory']
                    if os.path.exists(code_dir):
                        success = self._upload_lambda_code(function_name, code_dir, lambda_client)
                        if success:
                            print(f"Successfully updated Lambda function code: {function_name}")
                        else:
                            print(f"Warning: Failed to update code for: {function_name}")
                
                return True
            else:
                # Legacy format support
                function_name = content['FunctionName']
                response = lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    **{k: v for k, v in content.items() if k != 'FunctionName'}
                )
                print(f"Successfully updated Lambda function: {function_name}")
                return True
                
        except Exception as e:
            print(f"Error updating Lambda function: {e}")
            return False
    
    def _upload_lambda_code(self, function_name: str, code_dir: str, lambda_client) -> bool:
        """Upload Lambda function source code"""
        import zipfile
        import tempfile
        import os
        
        try:
            # Create a zip file with the code
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
                temp_zip_path = temp_zip.name
            
            try:
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(code_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, code_dir)
                            zip_file.write(file_path, arcname)
                
                # Upload the zip file
                with open(temp_zip_path, 'rb') as zip_file:
                    response = lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_file.read()
                    )
                
                return True
                
            finally:
                os.unlink(temp_zip_path)
                
        except Exception as e:
            print(f"Error uploading Lambda code: {e}")
            return False
    
    def display_selection_menu(self, functions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Display interactive menu for Lambda function selection"""
        if not functions:
            print("No Lambda functions found in this region.")
            return None
        
        print("\nAvailable Lambda Functions:")
        print("-" * 60)
        
        for i, func in enumerate(functions, 1):
            name = func['name']
            runtime = func['runtime']
            description = func.get('description', 'No description')
            
            print(f"{i}. [LAMBDA] {name}")
            print(f"    Runtime: {runtime}")
            print(f"    Description: {description[:80]}{'...' if len(description) > 80 else ''}")
            print(f"    Memory: {func.get('memory_size', 'N/A')} MB, Timeout: {func.get('timeout', 'N/A')}s")
        
        print(f"{len(functions) + 1}. Exit")
        
        try:
            choice = int(input("\nSelect a Lambda function to download (enter number): "))
            if 1 <= choice <= len(functions):
                return functions[choice - 1]
            elif choice == len(functions) + 1:
                return None
            else:
                print("Invalid selection.")
                return None
        except ValueError:
            print("Please enter a valid number.")
            return None


def main():
    parser = argparse.ArgumentParser(description='AWS Lambda Function Manager - List and manage AWS Lambda functions')
    parser.add_argument('--region', help='AWS region to list Lambda functions from (if not provided, will prompt)')
    parser.add_argument('--upload', help='Upload a modified Lambda function file')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    manager = LambdaFunctionManager(debug=args.debug)
    
    if args.upload:
        # Upload mode
        success = manager.upload_lambda_function(args.upload)
        if success:
            print("Upload completed successfully!")
        else:
            print("Upload failed!")
        return
    
    # List mode - get region
    region = args.region
    if not region:
        # Common AWS regions (us-west-2 first as default)
        common_regions = [
            'us-west-2', 'us-east-1', 'us-east-2', 'us-west-1',
            'eu-west-1', 'eu-west-2', 'eu-central-1', 'ap-southeast-1',
            'ap-southeast-2', 'ap-northeast-1'
        ]
        
        print("Select an AWS region:")
        for i, r in enumerate(common_regions, 1):
            default_marker = " (default)" if r == 'us-west-2' else ""
            print(f"{i}. {r}{default_marker}")
        print(f"{len(common_regions) + 1}. Enter custom region")
        print("\nPress Enter for default (us-west-2)")
        
        try:
            user_input = input("\nSelect a region (enter number): ").strip()
            if not user_input:  # Empty input, use default
                region = 'us-west-2'
            else:
                choice = int(user_input)
                if 1 <= choice <= len(common_regions):
                    region = common_regions[choice - 1]
                elif choice == len(common_regions) + 1:
                    region = input("Enter AWS region: ").strip()
                else:
                    print("Invalid selection.")
                    return
        except ValueError:
            print("Please enter a valid number.")
            return
    
    print(f"\nFetching Lambda functions in region: {region}")
    lambda_functions = manager.list_lambda_functions(region)
    
    # Show Lambda summary
    if lambda_functions:
        manager.display_lambda_summary(lambda_functions)
    
    while True:
        selected_function = manager.display_selection_menu(lambda_functions)
        if selected_function is None:
            break
        
        code_dir = manager.download_lambda_function(selected_function)
        
        if code_dir:
            print(f"\nLambda function code downloaded to: {code_dir}")
            print("You can now edit the source code files in this directory.")
    
    print("\nExiting...")


if __name__ == "__main__":
    main()