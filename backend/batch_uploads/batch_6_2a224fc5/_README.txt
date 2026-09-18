SDAIA / Hyland Text Extraction Dataset
========================================
Folder: dataset_large_1000
Generated files: 1000 (+ _manifest.csv, _README.txt)
Related to sdaia_quebook2.xlsx topics: 550
Unrelated baseline files: 450
Seed: 20260715

MIME / format coverage (Hyland Document Filters text-extractable):
  - .docx: application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - .pdf: application/pdf
  - .txt: text/plain
  - .html: text/html
  - .rtf: application/rtf
  - .csv: text/csv
  - .xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
  - .pptx: application/vnd.openxmlformats-officedocument.presentationml.presentation
  - .xml: text/xml
  - .eml: message/rfc822
  - .mht: multipart/related
  - .log: text/log
  - .json: application/json
  - .svg: image/svg+xml
  - .tsv: text/tab-separated-values
  - .md: text/markdown
  - .zip: application/zip

Notes:
- All documents are fictional and for PoC / classification testing only.
- Related files intentionally embed high-confidence keywords from the SDAIA question book.
- Unrelated files avoid those sensitivity themes.
- See _manifest.csv for ground-truth labels.
