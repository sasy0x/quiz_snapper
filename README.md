# QuizSnapper

**QuizSnapper** is a desktop application that captures screenshots, extracts text using OCR, and provides AI-powered answers to questions. Built with privacy in mind, it works entirely offline using local AI models.

## Features

- **Screenshot Capture**: Select any screen region with a customizable keyboard shortcut
- **OCR Text Extraction**: Extract text from images using Tesseract OCR (supports multiple languages)
- **AI-Powered Answers**: Get intelligent responses using local Ollama models or external APIs
- **MATCH Questions Support**: Automatically handles matching questions (A→1, B→2, etc.)
- **Multiple Question Types**: Multiple choice, true/false, short answer, and MATCH formats
- **PDF Knowledge Base**: Load PDF documents as reference material for more accurate answers
- **Smart Output Formatting**: Clean, readable answers with optional explanations
- **Transparent Popup**: Modern, less invasive UI with 95% transparency
- **Dual Close Buttons**: Subtle close buttons on both left and right sides
- **Draggable Window**: Click and drag title bar or title text to move popup
- **System Tray Integration**: Runs quietly in the background with easy access
- **Auto-Retry Logic**: Automatic retry on API failures (3 attempts)
- **Customizable Interface**: Configure popup position, size, transparency, and appearance
- **Privacy-Focused**: All processing happens locally by default
- **Debug Mode**: Enhanced logging with color-coded output for troubleshooting
- **Custom Tray Icons**: Choose from multiple icon styles (default, avast, spotify, etc.)

## Privacy & Security

- No data sent to external servers when using Ollama (local mode)
- Open source code - inspect and modify as needed
- No telemetry or tracking
- API keys never hardcoded in the repository

## Requirements

### System Requirements
- **Windows** 10/11 (primary support)
- **Python** 3.8 or higher
- **4GB RAM** minimum (8GB recommended for larger AI models)

### Required Software

1. **Tesseract OCR**
   - Download from: [UB Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
   - During installation, make sure to:
     - Install language packs (English + Italian recommended)
     - Add Tesseract to system PATH
   - Verify installation: `tesseract --version`

2. **Ollama** (for local AI)
   - Download from: [ollama.com/download](https://ollama.com/download)
   - Install and start the service
   - Verify it's running: Open browser to `http://localhost:11434`

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/jiovae/quiz_snapper.git
cd quiz_snapper
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Download AI Model

For local AI (Ollama):
```bash
ollama pull deepseek-r1:1.5b
```

For other models:
```bash
ollama pull llama2
ollama pull mistral
```

### Step 4: Create Knowledge Base Folder (Optional)

If you want to use PDF reference materials:
```bash
mkdir knowledge_base
```

Place your PDF files in this folder and enable `use_pdf_context` in config.json.

## Configuration

The `config.json` file controls all application settings. Here's a complete guide:

### General Settings

```json
{
  "shortcut": "ctrl+alt+x",
  "debug_mode": false,
  "log_file": "app.log"
}
```

- **shortcut**: Keyboard combination to trigger screenshot capture
- **debug_mode**: Enable detailed logging with colors (true/false)
- **log_file**: Path to log file

### System Tray

```json
{
  "tray_icon": "default",
  "tray_menu_title": "QuizSnapper"
}
```

- **tray_icon**: Icon filename without extension (place PNG files in `assets/` folder)
  - Options: `default`, `avast`, `spotify`, or any custom icon you add
- **tray_menu_title**: Text shown in system tray tooltip

### OCR Settings

```json
{
  "ocr_lang": "eng+ita"
}
```

- **ocr_lang**: Tesseract language codes (use + to combine multiple)
  - Examples: `eng`, `ita`, `eng+ita`, `fra+deu`

### Popup Window

```json
{
  "popup_position": "bottom_right",
  "popup_duration_ms": 7000,
  "popup_width": 420,
  "popup_height": 280,
  "popup_auto_close_delay_ms": 7000,
  "popup_transparency": 0.95
}
```

- **popup_position**: Where the popup appears on screen
  - Options: `bottom_right`, `top_right`, `bottom_left`, `top_left`, `center`
- **popup_duration_ms**: How long the popup stays visible (milliseconds)
- **popup_width**: Popup width in pixels (default: 420)
- **popup_height**: Popup height in pixels (default: 280)
- **popup_auto_close_delay_ms**: Auto-close delay (0 = never auto-close)
- **popup_transparency**: Window transparency (0.0 to 1.0, default: 0.95)

### AI Provider

```json
{
  "ai_provider": "ollama"
}
```

- **ai_provider**: Which AI service to use
  - `ollama`: Local AI (private, no internet required)
  - `api`: External API service (OpenRouter, OpenAI, etc.)

### Ollama Configuration (Local AI)

```json
{
  "ollama_model": "deepseek-r1:1.5b",
  "ollama_api_url": "http://localhost:11434/api/generate"
}
```

- **ollama_model**: Model name (must be pulled first with `ollama pull`)
- **ollama_api_url**: Ollama API endpoint (default is usually correct)

### External API Configuration (Optional)

```json
{
  "api_url": "https://openrouter.ai/api/v1/chat/completions",
  "api_key": "your-api-key-here",
  "api_model": "deepseek/deepseek-chat"
}
```

- **api_url**: API endpoint URL
- **api_key**: Your API key (keep this private!)
- **api_model**: Model identifier

### AI Prompt Template

```json
{
  "prompt_template": "You are an AI assistant helping with quiz questions. Analyze the following text extracted from a screenshot and provide a clear, concise answer.\n\nQuestion: [TEXT]\n\nProvide the correct answer with a brief explanation if needed.",
  "show_explanation": true,
  "clean_output": true
}
```

- **prompt_template**: Instructions sent to AI
- Use `[TEXT]` as placeholder for extracted text
- **show_explanation**: Include explanations in answers (true/false)
  - `true`: Full answer with explanation
  - `false`: Only the correct answer(s)
- **clean_output**: Remove "The correct answer is" and format nicely (true/false)

### PDF Knowledge Base

```json
{
  "use_pdf_context": false,
  "knowledge_base_folder": "knowledge_base"
}
```

- **use_pdf_context**: Enable PDF reference material (true/false)
- **knowledge_base_folder**: Folder containing PDF files

## Output Examples

### With Explanation (show_explanation: true)
```
• Eliminate waste

Lean methodology focuses on identifying and removing non-value-adding 
activities to improve efficiency and customer value.
```

### Without Explanation (show_explanation: false)
```
• Eliminate waste
```

### Multiple Answers
```
• TCP (Transmission Control Protocol)
• UDP (User Datagram Protocol)
```

### MATCH Questions
```
A → 2
B → 3
C → 1
D → 4
```

The output is automatically cleaned to remove phrases like "The correct answer is" and formatted appropriately for each question type. See [MATCH_EXAMPLES.md](MATCH_EXAMPLES.md) for detailed MATCH question examples.

## Usage

### Starting the Application

**Console Mode** (with debug output):
```bash
python -m src.main
```

**Background Mode** (no console window):
```bash
pythonw -m src.main
```

**With Debug Mode**:
```bash
# Edit config.json and set "debug_mode": true
python -m src.main
```

### Using QuizSnapper

1. **Start the application** - An icon appears in your system tray
2. **Press the hotkey** (default: `Ctrl+Alt+X`) or right-click tray icon → "Capture Screenshot"
3. **Select screen area** - Click and drag to select the region containing your question
4. **Wait for processing** - OCR extracts text, AI generates answer
5. **View answer** - A popup window shows the AI's response
6. **Close popup** - Click X or wait for auto-close

### System Tray Menu

Right-click the tray icon to access:
- **Capture Screenshot**: Manually trigger capture
- **Open Configuration**: Edit config.json
- **View Logs**: Open log file
- **Exit**: Close the application

## Adding Custom Tray Icons

1. Create a PNG image (64x64 pixels recommended)
2. Save it in the `assets/` folder (e.g., `assets/myicon.png`)
3. Edit `config.json`:
   ```json
   {
     "tray_icon": "myicon"
   }
   ```
4. Restart the application

## Using PDF Knowledge Base

1. Create a `knowledge_base` folder in the project root
2. Add PDF files with relevant information
3. Enable in `config.json`:
   ```json
   {
     "use_pdf_context": true
   }
   ```
4. The AI will use PDF content to answer questions

## Troubleshooting

### Tesseract Not Found

**Problem**: Error message about Tesseract not being installed

**Solutions**:
- Verify installation: `tesseract --version` in command prompt
- Check PATH: Tesseract should be in system PATH
- Reinstall Tesseract and ensure "Add to PATH" is checked
- Restart computer after installation

### Ollama Connection Error

**Problem**: Cannot connect to Ollama service

**Solutions**:
- Check if Ollama is running: Open `http://localhost:11434` in browser
- Start Ollama service (usually starts automatically)
- Verify model is downloaded: `ollama list`
- Check firewall isn't blocking port 11434

### Hotkey Not Working

**Problem**: Keyboard shortcut doesn't trigger capture

**Solutions**:
- Check if another application uses the same shortcut
- Try a different combination in `config.json`
- Run application as administrator (some apps block global hotkeys)
- Restart the application after changing shortcuts

### OCR Accuracy Issues

**Problem**: Text extraction is inaccurate

**Solutions**:
- Ensure screenshot has good contrast and resolution
- Install additional Tesseract language packs
- Capture larger screen area for more context
- Use `eng+ita` or appropriate language combination

### Popup Not Appearing

**Problem**: Answer popup doesn't show

**Solutions**:
- Check debug mode logs for errors
- Verify popup position isn't off-screen
- Try changing `popup_position` in config
- Check if popup is behind other windows

### API Errors

**Problem**: External API returns errors

**Solutions**:
- Verify API key is correct and active
- Check API quota/credits
- Ensure `api_url` matches your provider
- Test API key with provider's documentation

## Debug Mode

Enable enhanced debugging:

1. Edit `config.json`:
   ```json
   {
     "debug_mode": true
   }
   ```

2. Run in console mode:
   ```bash
   python -m src.main
   ```

3. Debug output includes:
   - Color-coded log messages
   - API request/response details
   - OCR extracted text
   - Timing information

## Project Structure

```
quiz_snapper/
├── assets/              # Icon files
│   ├── default.png
│   ├── avast.png
│   └── spotify.png
├── knowledge_base/      # PDF reference materials (optional)
├── src/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── config_manager.py # Configuration handling
│   ├── gui.py           # System tray and popup UI
│   ├── screenshot.py    # Screen capture functionality
│   ├── ocr.py           # Text extraction
│   ├── ollama_integration.py # AI integration
│   └── utils.py         # Logging and utilities
├── config.json          # User configuration
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .gitignore          # Git ignore rules
```

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Acknowledgments

- **Tesseract OCR**: Google's open-source OCR engine
- **Ollama**: Local AI model runtime
- **PyPDF2**: PDF text extraction
- **pystray**: System tray integration

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Enable debug mode for detailed error information

---

**Note**: This application is designed for educational and productivity purposes. Ensure you comply with your institution's or organization's policies regarding AI assistance tools.
