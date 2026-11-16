Tarot JupyterLab
 
An English sidebar extension for JupyterLab 4. Draw a tarot card, request an AI reading, and save the most recent result locally. (Tarot readings are for entertainment and self-reflection purposes.)
1. Features‌
• Interactive Sidebar: Seamlessly draw tarot cards directly within JupyterLab.
• AI-Powered Reading: Get interpretations using any OpenAI-compatible service.
• Local Storage: Automatically saves your most recent results locally.
• Flexible Configuration: Easy setup via UI settings or environment variables.‌
2. Installation
Execute the following commands in an isolated Python environment. Replace the filename with the actual downloaded .whl file: 
python -m venv .venv
..venv\Scripts\python.exe -m pip install "jupyterlab==4.6.5" ".\tarot_jupyterlab-0.1.0-py3-none-any.whl"
3. Usage
4. Launch JupyterLab using the command below:
..venv\Scripts\python.exe -m jupyterlab
5. Open the Tarot tab on the left sidebar.
6. Enter a sample question and click Draw a card to draw and save.
7. Restart JupyterLab and click View latest to see the saved results.
8. Screenshots
(Please drag and drop a screenshot of the Tarot sidebar here)
9. AI Configuration
You can configure the AI settings in two ways: 
Option A: UI Settings
Click AI settings at the top of the sidebar, check Enable AI readings, and fill in your Base URL, model, and API key.
 
Option B: Environment Variables
Configure the AI before starting JupyterLab:
TAROT_AI_BASE_URL: The API base URL for OpenAI-compatible services.
TAROT_AI_ENABLED: Set to 0 to disable AI features. 

