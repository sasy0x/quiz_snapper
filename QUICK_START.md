# QuizSnapper v1.3.0 - Quick Start Guide

Get up and running with QuizSnapper in 5 minutes!

## Prerequisites

Before you start, make sure you have:

- ✅ **Windows 10/11**
- ✅ **Python 3.8+** installed
- ✅ **Tesseract OCR** installed ([Download here](https://github.com/UB-Mannheim/tesseract/wiki))
- ✅ **Ollama** installed ([Download here](https://ollama.com/download))

## Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/quiz_snapper.git
cd quiz_snapper

# Run setup
setup.bat
```

Or manually:
```bash
pip install -r requirements.txt
```

## Step 2: Download AI Model

```bash
ollama pull deepseek-r1:1.5b
```

This downloads a lightweight AI model (~1GB). For better accuracy, try:
```bash
ollama pull llama2
```

## Step 3: Configure (Optional)

The default configuration works out of the box, but you can customize:

```json
{
  "shortcut": "ctrl+alt+x",
  "auto_select_enabled": false,
  "ai_provider": "ollama"
}
```

## Step 4: Start QuizSnapper

**Background Mode** (recommended):
```bash
start.bat
```

**Debug Mode** (see logs):
```bash
start_debug.bat
```

Look for the QuizSnapper icon in your system tray (bottom-right corner).

## Step 5: Use It!

1. **Open your quiz** in a browser or application
2. **Press `Ctrl+Alt+X`** (or your configured shortcut)
3. **Select the question area** - a semi-transparent overlay appears
4. **Click and drag** to select the region with your question
5. **Wait 2-3 seconds** for OCR and AI processing
6. **View the answer** in the popup window

### New in v1.3.0:
- **Enhanced Matching Questions**: Clear format showing what matches with what
- **Keyboard Toggle**: Press `Ctrl+Alt+A` to enable/disable auto-selector
- **Better Accuracy**: Improved prompts and OCR preprocessing

## Using Auto-Select

To automatically click answers:

**Method 1 - Tray Icon**:
1. **Right-click** the tray icon
2. **Click "Auto-Select Answers"** to enable (checkmark appears)

**Method 2 - Keyboard** (NEW):
1. **Press `Ctrl+Alt+A`** to toggle on/off
2. A notification popup confirms the state

**Features**:
- ✅ Single answer questions
- ✅ Multiple answer questions (selects ALL correct answers)
- ✅ True/False questions
- ❌ Matching questions (shows answer but doesn't auto-select)

**Safety**: Move mouse to any corner to stop auto-clicking.

## Common Issues

### "Tesseract not found"
- Install Tesseract OCR
- Make sure it's added to system PATH
- Restart your computer

### "Cannot connect to Ollama"
- Make sure Ollama is running
- Open http://localhost:11434 in browser to verify
- Restart Ollama service

### "Hotkey not working"
- Try a different shortcut in config.json
- Run as administrator
- Check if another app uses the same shortcut

## Next Steps

- 📖 Read the [full README](README.md) for advanced features
- 🔧 Customize your [configuration](README.md#configuration)
- 📚 Add PDFs to `knowledge_base/` folder for better answers
- 🎨 Add custom tray icons to `assets/` folder

## Tips for Best Results

1. **Capture clear text**: Make sure the question is readable
2. **Use good contrast**: Dark text on light background works best
3. **Include context**: Capture the full question, not just part of it
4. **Enable debug mode**: Helps troubleshoot issues
5. **Try different models**: Some models work better for specific subjects

## Getting Help

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/sasy0x/quiz_snapper/issues)
- 💬 [Ask Questions](https://github.com/sasy0x/quiz_snapper/discussions)

---

**Enjoy QuizSnapper! 🎉**
