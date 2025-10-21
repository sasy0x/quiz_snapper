# QuizSnapper v1.2.0

**QuizSnapper** is a desktop application that captures screenshots, extracts text using OCR, and provides AI-powered answers to questions. Built with privacy in mind, it works entirely offline using local AI models.

## What's New in v1.2.0

- **Enhanced AI Accuracy**: Improved prompt engineering for more precise single-answer responses
- **Smart Answer Detection**: AI automatically detects when multiple answers are required based on question wording
- **Advanced OCR Processing**: Image upscaling, grayscale conversion, contrast enhancement, and sharpening for better text recognition
- **Small Text Support**: Automatic upscaling for images with small text (< 1000x600px)
- **Improved Fuzzy Matching**: Enhanced algorithm for better answer detection with OCR errors
- **Real-time Config Updates**: Settings changes apply immediately without restart
- **Optimized Output Formatting**: Cleaner answer presentation with better Unicode handling

## Features

### Core Features
- **Screenshot Capture**: Select any screen region with a customizable keyboard shortcut
- **OCR Text Extraction**: Extract text from images using Tesseract OCR (supports multiple languages)
- **AI-Powered Answers**: Get intelligent responses using local Ollama models or external APIs
- **Auto-Select Answers** ⭐ NEW: Automatically clicks correct answers on screen for multiple choice and true/false questions

### Question Support
- **Multiple Choice**: Single and multiple answer questions (AI detects when multiple answers are needed)
- **True/False**: Boolean questions
- **Short Answer**: Text-based responses
- **MATCH Questions**: Displays matching pairs (auto-selection not supported)

### Advanced Features
- **PDF Knowledge Base**: Load PDF documents as reference material for more accurate answers
- **Smart Output Formatting**: Clean, readable answers with optional explanations
- **System Tray Integration**: Runs quietly in the background with easy access
- **Auto-Retry Logic**: Automatic retry on API failures (3 attempts)
- **Privacy-Focused**: All processing happens locally by default

### User Interface
- **Transparent Popup**: Modern, less invasive UI with 95% transparency
- **Draggable Window**: Click and drag title bar to move popup
- **Customizable Interface**: Configure popup position, size, transparency, and appearance
- **Custom Tray Icons**: Choose from multiple icon styles
- **Debug Mode**: Enhanced logging with color-coded output for troubleshooting

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
  "version": "1.2.0",
  "shortcut": "ctrl+alt+x",
  "debug_mode": false,
  "log_file": "app.log"
}
```

- **version**: Application version
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
  "popup_enabled": true,
  "popup_position": "bottom_right",
  "popup_duration_ms": 7000,
  "popup_width": 420,
  "popup_height": 280,
  "popup_auto_close_delay_ms": 7000,
  "popup_transparency": 0.95
}
```

- **popup_enabled** ⭐: Show/hide answer popup window (true/false)
  - When disabled, answers are only logged (useful with auto-select)
  - Can be toggled from tray menu
- **popup_position**: Where the popup appears on screen
  - Options: `bottom_right`, `top_right`, `bottom_left`, `top_left`, `center`
- **popup_duration_ms**: How long the popup stays visible (milliseconds)
- **popup_width**: Popup width in pixels (default: 420)
- **popup_height**: Popup height in pixels (default: 280)
- **popup_auto_close_delay_ms**: Auto-close delay (0 = never auto-close)
- **popup_transparency**: Window transparency (0.0 to 1.0, default: 0.95)

### Auto-Select Feature ⭐

```json
{
  "auto_select_enabled": false
}
```

- **auto_select_enabled**: Enable automatic answer selection (true/false)
  - When enabled, QuizSnapper will automatically click correct answers on screen
  - Works for multiple choice (radio/checkbox) and true/false questions
  - Supports multiple correct answers when explicitly required
  - Can be toggled in real-time from the system tray menu
  - **How it works**: Uses OCR to locate answer text on screen and clicks radio buttons
  - **Smart matching**: Exact match priority, fuzzy matching for typos, handles OCR errors
  - **Requirements**: Answers must be visible as text on screen
  - **Safety**: PyAutoGUI fail-safe enabled (move mouse to corner to stop)
  - **Note**: MATCH questions show answers in popup but auto-selection is not supported

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
  "prompt_template": "You are a quiz assistant. Analyze the question and provide ONLY the correct answer.\n\nFor MULTIPLE CHOICE: Provide ONLY the correct option text (not all options). If multiple answers are required, the question will explicitly state 'select all that apply' or 'choose two' - only then provide multiple answers.\nFor MATCH questions: Show connections as 'A → 1', 'B → 2', etc.\nFor TRUE/FALSE: State True or False\nFor SHORT ANSWER: Provide the direct answer\n\nQuestion: [TEXT]\n\nAnswer:",
  "show_explanation": true,
  "clean_output": true
}
```

- **prompt_template**: Instructions sent to AI (optimized to return only correct answers)
- Use `[TEXT]` as placeholder for extracted text
- **show_explanation** ⭐: Include explanations in answers (true/false)
  - `true`: Correct answer with brief explanation of why it's correct
  - `false`: Only the correct answer(s)
  - Can be toggled from tray menu
- **clean_output**: Remove prefixes like "The correct answer is" and format nicely (true/false)

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
3. **Select screen area** - A nearly transparent overlay (90% transparent) appears with cyan border
   - Click and drag to select the region containing your question
   - Minimal visual impact for stealth operation
4. **Wait for processing** - OCR extracts text, AI generates answer
5. **View answer** - A popup window shows the AI's response (if enabled)
6. **Close popup** - Click X or wait for auto-close

### System Tray Menu

Right-click the tray icon to access:
- **Capture Screenshot**: Manually trigger capture
- **Auto-Select Answers** ⭐: Toggle automatic answer selection on/off
- **Show Popup** ⭐: Toggle answer popup window on/off
- **Show Explanation** ⭐: Toggle detailed explanations in answers
- **Open Configuration**: Edit config.json
- **View Logs**: Open log file
- **Exit**: Close the application

All toggles show a checkmark when enabled and save immediately to config.

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

### Auto-Select Not Working

**Problem**: Auto-select feature doesn't click answers

**Solutions**:
- Ensure auto-select is enabled in tray menu (checkmark visible)
- Verify answers are visible as text on screen (not images)
- Check that question type is supported (multiple choice or true/false)
- MATCH questions are not supported for auto-selection
- Enable debug mode to see detection logs
- Ensure no other windows are covering the quiz
- Move mouse to screen corner to trigger fail-safe if needed

### OCR Not Accurate

**Problem**: Text extraction is inaccurate or incomplete

**Solutions**:
- Capture a larger screen area for better context
- Ensure good contrast between text and background
- For small text: QuizSnapper automatically upscales images < 1000x600px
- Try capturing with more zoom if possible
- Install additional Tesseract language packs if needed

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
│   ├── auto_selector.py # Auto-select answers (multiple choice & true/false)
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
