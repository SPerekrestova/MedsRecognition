const form = document.getElementById('upload-form');
const imageInput = document.getElementById('image-input');
const loader = document.getElementById('loader');
const preview = document.getElementById('preview');
const resultDiv = document.getElementById('result');
const extractedTextP = document.getElementById('extracted-text');
const activeIngredientsUl = document.getElementById('active-ingredients');

const API_URL = 'http://localhost:8000';

form.addEventListener('submit', async function(event) {
    event.preventDefault();

    const file = imageInput.files[0];
    if (!file) {
        alert('Please select an image file.');
        return;
    }

    const reader = new FileReader();
    reader.onload = function(e) {
        preview.src = e.target.result;
        preview.style.display = 'block';
    }
    reader.readAsDataURL(file);

    loader.style.display = 'block';
    resultDiv.style.display = 'none';

    const formData = new FormData();
    formData.append('image', file);

    try {
        const response = await fetch(API_URL + '/upload/', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const data = await response.json();

        loader.style.display = 'none';

        extractedTextP.textContent = data.text;

        activeIngredientsUl.innerHTML = '';
        if (data.active_ingredients && data.active_ingredients.length > 0) {
            data.active_ingredients.forEach(ingredient => {
                const li = document.createElement('li');
                li.textContent = ingredient;
                activeIngredientsUl.appendChild(li);
            });
        } else {
            activeIngredientsUl.innerHTML = '<li>No active ingredients found.</li>';
        }

        resultDiv.style.display = 'block';
    } catch (error) {
        console.error('Error:', error);
        loader.style.display = 'none';
        alert('An error occurred while processing the image. Please try again.');
    }
});
