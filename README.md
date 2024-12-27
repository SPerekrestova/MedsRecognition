# MedsRecognition

**MedsRecognition** is a Django-based application that extracts text from uploaded images using EasyOCR and identifies active ingredients in medications by querying a public database provided by RxNav. 

> **Note:** This project is a work in progress. Some features may not yet be fully implemented or finalized.

---

## Table of Contents
1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation](#installation)  
4. [How It Works](#how-it-works)  
5. [Usage](#usage)  
6. [Contact](#contact)

---

## Features
- Upload an image to extract text.  
- Supports various image formats (JPEG, PNG, etc.).  
- Leverages EasyOCR for highly accurate text recognition.  
- Matches recognized text with a database of active ingredients from RxNav, a public resource.  

---

## Prerequisites
- Python 3.8+  
- Pip (Python package manager)  

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SPerekrestova/MedsRecognition.git
   cd text-recognition
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Apply migrations (if applicable):  
   If your app uses models and migrations, run:  
   ```bash
   python manage.py migrate
   ```  
   If no migrations are needed, skip this step.

4. Run the Django server:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

---

## How It Works

1. **Upload Image**:  
   - The user uploads an image containing text via the web interface.  
   - Supported formats include JPEG, PNG, and others.  

2. **Text Recognition**:  
   - The uploaded image is processed by the EasyOCR library, which extracts text using pre-trained deep learning models.  
   - EasyOCR identifies characters and words from the image, ensuring accuracy across multiple languages.  

3. **Querying RxNav Database**:  
   - Recognized text is matched against a list of active ingredients obtained from the RxNav public database.  
   - The application queries RxNav’s API to fetch and update the list of active ingredients when needed.  
   - This ensures up-to-date and reliable information for matching.  

4. **Display Results**:  
   - Once the text is extracted and matched with active ingredients, the results are displayed on a dedicated page.  
   - Users can view the identified active ingredients or copy them for further use.  

5. **Behind the Scenes**:  
   - The Django application handles image uploads and server-side processing.  
   - EasyOCR performs text recognition, while RxNav API integration ensures accurate identification of active ingredients.  

---

## Usage

1. Launch the application by running the Django server:
   ```bash
   python manage.py runserver
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:8000/
   ```

3. Upload an image containing text.  
4. The extracted text will be displayed on the results page along with matched active ingredients.

---

## Contact

**Author**: Svetlana Perekrestova  
**Email**: [svetlana.perekrestova2@gmail.com](mailto:svetlana.perekrestova2@gmail.com)  

---
