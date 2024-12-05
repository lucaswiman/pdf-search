class PdfUploader extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.render();
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .uploader {
                    margin: 20px 0;
                    padding: 20px;
                    border: 2px dashed #ccc;
                    border-radius: 4px;
                }
                .message {
                    margin-top: 10px;
                    color: #666;
                }
            </style>
            <div class="uploader">
                <input type="file" accept=".pdf" id="fileInput">
                <button id="uploadBtn">Upload PDF</button>
                <div class="message"></div>
            </div>
        `;

        this.shadowRoot.querySelector('#uploadBtn').addEventListener('click', () => this.uploadFile());
    }

    async uploadFile() {
        const fileInput = this.shadowRoot.querySelector('#fileInput');
        const messageDiv = this.shadowRoot.querySelector('.message');
        
        if (!fileInput.files.length) {
            messageDiv.textContent = 'Please select a file first';
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const response = await fetch('/upload/', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                messageDiv.textContent = `Success: ${result.pages_processed} pages processed`;
                // Dispatch event to notify pdf-viewer
                this.dispatchEvent(new CustomEvent('pdf-uploaded', {
                    bubbles: true,
                    composed: true,
                    detail: { filename: result.filename }
                }));
            } else {
                messageDiv.textContent = `Error: ${result.detail}`;
            }
        } catch (error) {
            messageDiv.textContent = `Error: ${error.message}`;
        }
    }
}

customElements.define('pdf-uploader', PdfUploader);
