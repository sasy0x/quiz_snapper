# Knowledge Base Folder

Place PDF files in this folder to use them as reference material for AI answers.

## How to Use

1. Add PDF files to this folder
2. Enable PDF context in `config.json`:
   ```json
   {
     "use_pdf_context": true
   }
   ```
3. Restart QuizSnapper

## Supported Formats

- PDF files (.pdf)
- Text-based PDFs work best
- Scanned PDFs may have limited text extraction

## Tips

- Organize PDFs by topic
- Use descriptive filenames
- Keep file sizes reasonable (< 50MB per file)
- The AI will search all PDFs in this folder for relevant information

## Examples

Good filenames:
- `networking_fundamentals.pdf`
- `python_programming_guide.pdf`
- `calculus_formulas.pdf`

The AI will use content from these PDFs to provide more accurate, context-aware answers to your questions.
