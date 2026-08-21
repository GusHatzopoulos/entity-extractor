# Entity Extractor

A Python tool for extracting, normalizing, classifying, and indexing named entities from documents, spreadsheets, presentations, structured data, and images using Natural Language Processing (NLP) and Optical Character Recognition (OCR).

Entity Extractor provides a unified pipeline for processing different file formats and identifying useful entities such as people, locations, organizations, companies, events, and custom names.

The project is designed to work with both standard text-based files and image-based content, making it suitable for large document collections, manuscripts, reports, datasets, presentations, scanned documents, and images.

## Features

* Multi-format file processing
* Named Entity Recognition (NER)
* OCR-based text extraction from images
* OCR support for scanned PDFs
* Character and person name extraction
* Location detection
* Organization and company detection
* Custom and fictional entity detection
* Entity occurrence counting
* Duplicate detection
* Spelling and accent normalization
* Entity variant matching
* Entity classification
* Multi-file processing
* Structured result export
* Local file processing
* Original source files remain unchanged

## Supported Input Formats

### Documents

* `.docx`
* `.pdf`
* `.txt`

### Spreadsheets

* `.xls`
* `.xlsx`

### Presentations

* `.pptx`

### Structured Data

* `.xml`

### Images

* `.png`
* `.jpg`
* `.jpeg`
* `.tiff`
* `.bmp`
* `.webp`

### Scanned Documents

Scanned or image-based PDF documents can be processed through the OCR pipeline when no usable text layer is available.

## Entity Types

Entity Extractor is designed to identify and classify entities such as:

* `PERSON`
* `LOCATION`
* `ORGANIZATION`
* `COMPANY`
* `EVENT`
* `PRODUCT`
* `CUSTOM`
* `UNKNOWN`

Custom entity detection is intended to improve support for domain-specific terminology, fictional characters, fictional locations, invented organizations, and other names that may not be recognized reliably by standard NER models.

## Processing Pipeline

```text
                         INPUT
                           │
          ┌────────────────┼────────────────┐
          │                │                │
      Documents        Structured         Images
          │                │                │
 DOCX / PDF / TXT      XML / XLS(X)    PNG / JPG / TIFF
      / PPTX               │             BMP / WEBP
          │                │                │
          │                │               OCR
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                  Unified Text Layer
                           │
                           ▼
                   Entity Detection
                           │
              ┌────────────┼────────────┐
              │            │            │
             NER       Rule-Based     Custom
                        Detection     Detection
              │            │            │
              └────────────┼────────────┘
                           ▼
                     Normalization
                           │
                ┌──────────┴──────────┐
                │                     │
          Duplicate Detection    Variant Matching
                │                     │
                └──────────┬──────────┘
                           ▼
                    Classification
                           │
                           ▼
                  Frequency Analysis
                           │
                           ▼
                    Structured Export
```

## Example Output

| Entity          | Type         | Occurrences | Variants        | Source            |
| --------------- | ------------ | ----------: | --------------- | ----------------- |
| Example Name    | PERSON       |         124 | Example variant | manuscript.docx   |
| Example City    | LOCATION     |          67 | —               | report.pdf        |
| Example Company | COMPANY      |          31 | Example Co.     | records.xlsx      |
| Example Order   | ORGANIZATION |          18 | —               | presentation.pptx |

## Project Structure

```text
entity-extractor/
│
├── data/
│   └── input/
│
├── output/
│
├── src/
│   ├── extractors/
│   │   ├── docx_extractor.py
│   │   ├── pdf_extractor.py
│   │   ├── txt_extractor.py
│   │   ├── excel_extractor.py
│   │   ├── pptx_extractor.py
│   │   ├── xml_extractor.py
│   │   └── image_extractor.py
│   │
│   ├── entity/
│   │   ├── detector.py
│   │   ├── normalizer.py
│   │   └── classifier.py
│   │
│   └── exporters/
│       └── excel_exporter.py
│
├── tests/
│
├── main.py
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/entity-extractor.git
cd entity-extractor
```

Create a virtual environment.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Place supported files inside:

```text
data/input/
```

Run the application:

```bash
python main.py
```

Processed results will be written to:

```text
output/
```

## OCR Processing

For image-based files, Entity Extractor first performs Optical Character Recognition to obtain machine-readable text.

```text
Image / Scanned PDF
        │
        ▼
       OCR
        │
        ▼
 Extracted Text
        │
        ▼
 Entity Detection
```

OCR accuracy depends on factors such as image resolution, document quality, language, typography, orientation, and scan quality.

## Entity Normalization

Detected entities may appear in different forms throughout a source document.

The normalization pipeline is intended to identify and consolidate variations caused by:

* Capitalization
* Accents
* Minor spelling differences
* Abbreviations
* Alternative forms
* OCR inconsistencies

The original detected forms can be preserved as variants while a normalized entity is used for indexing and frequency analysis.

## Output

Structured results can include:

* Entity name
* Entity type
* Number of occurrences
* Detected variants
* Source filename
* Source location
* Extraction method

Planned export formats include:

* `.xlsx`
* `.csv`
* `.json`

## Privacy

Entity Extractor is designed around local file processing.

Input documents may contain private, copyrighted, confidential, or otherwise sensitive information. Source files and generated output containing extracted information should not be committed to a public repository.

The `data/` and `output/` directories should therefore be excluded from version control where appropriate.

## Development Roadmap

### Phase 1 — Core

* [ ] Project architecture
* [ ] File type detection
* [ ] Unified extraction interface
* [ ] TXT extraction
* [ ] DOCX extraction

### Phase 2 — Document Support

* [ ] PDF extraction
* [ ] XLSX extraction
* [ ] XLS extraction
* [ ] PPTX extraction
* [ ] XML extraction

### Phase 3 — Image & OCR

* [ ] Image ingestion
* [ ] OCR pipeline
* [ ] OCR language configuration
* [ ] Scanned PDF detection
* [ ] Scanned PDF OCR

### Phase 4 — Entity Extraction

* [ ] Named Entity Recognition
* [ ] Person detection
* [ ] Location detection
* [ ] Organization detection
* [ ] Custom entity detection
* [ ] Fictional-name detection

### Phase 5 — Data Processing

* [ ] Entity normalization
* [ ] Duplicate detection
* [ ] Variant matching
* [ ] Frequency analysis
* [ ] Source tracking

### Phase 6 — Export

* [ ] Excel export
* [ ] CSV export
* [ ] JSON export

### Phase 7 — Quality

* [ ] Unit tests
* [ ] Integration tests
* [ ] Large-document testing
* [ ] OCR accuracy testing
* [ ] Documentation
* [ ] Error handling and logging

## Technologies

The project is expected to use Python libraries and tools for:

* DOCX parsing
* PDF parsing
* Excel processing
* PowerPoint processing
* XML parsing
* OCR
* Natural Language Processing
* Named Entity Recognition
* Structured data export

Specific dependencies will be documented as they are introduced during development.

## Project Status

**Early Development**

The initial implementation focuses on establishing the multi-format extraction architecture before expanding the NLP, OCR, normalization, and export pipelines.

## License

License information will be added as the project develops.


