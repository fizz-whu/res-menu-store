# Amazon Lex Bot Manager

A Python tool to easily download, edit, and upload Amazon Lex bot components including intents, slots, and Lambda functions.

## Features

- Read bot IDs from CSV file
- List and select bot components (intents, slots, Lambda functions)
- Download components as JSON files for editing
- Upload modified components back to Lex
- Organized folder structure for downloads

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure AWS credentials:
```bash
aws configure
```

3. Prepare your CSV file with bot IDs (see `bot_ids.csv` example)

## Usage

### Download Mode (Interactive)
```bash
python lex_bot_manager.py
```

Or specify a different CSV file:
```bash
python lex_bot_manager.py --csv my_bots.csv
```

This will:
1. Show you available bots from the CSV with their regions
2. Let you select a bot
3. Display all components (intents, slots, Lambda functions)
4. Allow you to download selected components

### Upload Mode
```bash
python lex_bot_manager.py --upload ./lex_downloads/BOTID/intents/WelcomeIntent.json
```

### Debug Mode
```bash
python lex_bot_manager.py --debug
```

This will show detailed information about the Lambda function detection process, including:
- Which intents are being checked
- What code hooks are found
- Lambda function ARNs discovered
- Available functions in the region (for reference)

### Include Fallback Functions
```bash
python lex_bot_manager.py --include-fallback
```

By default, the tool only shows Lambda functions that are directly connected to the bot through intent hooks. Use this flag to also include functions found by name/description matching.

### Export Bot Definition
```bash
python lex_bot_manager.py --export-bot
```

This exports the complete bot definition as JSON and analyzes it comprehensively for Lambda function references. This method is more thorough than intent-by-intent analysis and can find Lambda functions in:
- Intent fulfillment hooks
- Dialog management hooks
- Confirmation/declination hooks
- Initial/closing responses
- Any other bot configuration areas

### Combined Options
```bash
python lex_bot_manager.py --debug --export-bot --include-fallback
```

## CSV Format

Your CSV file should have `bot_id` and `region` columns:

```csv
bot_id,bot_name,description,region
ABCD1234,CustomerServiceBot,Main customer service bot,us-east-1
EFGH5678,OrderBot,Bot for handling orders,us-west-2
```

The tool will automatically use `bot_ids.csv` as the default filename.

## File Structure

Downloaded components are organized as:
```
lex_downloads/
├── BOTID1/
│   ├── intents/
│   │   ├── WelcomeIntent.json
│   │   └── OrderIntent.json
│   ├── slots/
│   │   └── ProductType.json
│   └── lambda_functions/
│       ├── OrderProcessor.json          # Function configuration
│       └── OrderProcessor_code/         # Source code directory
│           ├── lambda_function.py       # Main handler
│           ├── requirements.txt         # Dependencies
│           └── ...                      # Other source files
└── BOTID2/
    └── ...
```

## Workflow

1. **Download**: Use the tool to download components you want to modify
2. **Edit**: Edit the downloaded JSON files and/or Lambda source code
3. **Upload**: Use the upload mode to push your changes back to Lex

## Lambda Function Handling

The tool has enhanced Lambda function support:

### Lambda Function Detection
- **Intent-by-Intent Analysis**: Scans all intents for fulfillment and dialog code hooks (default)
- **Complete Bot Export**: Use `--export-bot` to analyze the entire bot definition JSON for comprehensive Lambda detection
- **Optional Fallback Search**: Use `--include-fallback` to also find functions by name/description matching
- **Only Actually Used Functions**: By default, shows only Lambda functions directly connected to the bot
- **Usage Tracking**: Shows exactly where each Lambda function is used

### Lambda Function Downloads
- **Configuration**: Downloads function settings (timeout, memory, environment variables, etc.)
- **Source Code**: Downloads and extracts the actual Lambda function code
- **Organized Structure**: Creates separate directories for config and code

### Lambda Function Modifications
- **Configuration Changes**: Edit the `.json` file to modify function settings
- **Code Changes**: Edit files in the `_code/` directory to modify function logic
- **Full Upload**: Both configuration and code changes are uploaded when using `--upload`

### Lambda Function Usage Display

The tool shows detailed information about where each Lambda function is used:

- **🎯 Fulfillment Functions**: Handle the final action after all slots are filled
- **💬 Dialog Functions**: Manage conversation flow and slot validation
- **Connection Types**:
  - `DIRECT`: Functions directly connected to intents
  - `INFERRED`: Functions found by name/description matching
  - `DEBUG`: Functions added for debugging purposes

### Lambda Function Locations
Lambda functions are stored in:
```
lex_downloads/BOTID/lambda_functions/
├── FunctionName.json          # Configuration (timeout, memory, env vars)
└── FunctionName_code/         # Source code directory
    ├── lambda_function.py     # Your handler code
    ├── requirements.txt       # Dependencies
    └── other_files...         # Additional source files
```

## Important Notes

- Always test your changes in a development environment first
- The tool works with bot versions - make sure you're editing the correct version
- Lambda function uploads update both configuration AND source code
- Some fields are automatically excluded from downloads to prevent conflicts

## AWS Permissions Required

Your AWS credentials need the following permissions:
- `lex:DescribeBot`
- `lex:ListBotVersions`
- `lex:ListBotLocales`
- `lex:ListIntents`
- `lex:ListSlotTypes`
- `lex:DescribeIntent`
- `lex:DescribeSlotType`
- `lex:UpdateIntent`
- `lex:UpdateSlotType`
- `lambda:ListFunctions`
- `lambda:GetFunction`
- `lambda:UpdateFunctionConfiguration`