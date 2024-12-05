class PdfViewer extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.render();
    }

    connectedCallback() {
        window.addEventListener('pdf-uploaded', (e) => this.loadDocument(e.detail.filename));
    }

    render() {
        this.shadowRoot.innerHTML = `
            <style>
                .viewer {
                    margin: 20px 0;
                }
                .search-box {
                    margin-bottom: 20px;
                }
                .page {
                    margin: 10px 0;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .page-number {
                    font-weight: bold;
                    color: #666;
                }
            </style>
            <div class="viewer">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search PDFs...">
                    <button id="searchBtn">Search</button>
                </div>
                <div id="content"></div>
            </div>
        `;

        this.shadowRoot.querySelector('#searchBtn').addEventListener('click', () => this.searchContent());
    }

    async loadDocument(filename) {
        const contentDiv = this.shadowRoot.querySelector('#content');
        try {
            const response = await fetch(`/document/${filename}`);
            const pages = await response.json();
            
            contentDiv.innerHTML = pages.map(page => `
                <div class="page">
                    <div class="page-number">Page ${page.page_number}</div>
                    <div class="content">${page.content}</div>
                </div>
            `).join('');
        } catch (error) {
            contentDiv.innerHTML = `Error loading document: ${error.message}`;
        }
    }

    async searchContent() {
        const searchInput = this.shadowRoot.querySelector('#searchInput');
        const contentDiv = this.shadowRoot.querySelector('#content');
        const query = searchInput.value.trim();
        
        if (!query) return;

        try {
            const response = await fetch(`/search/${encodeURIComponent(query)}`);
            const results = await response.json();
            
            contentDiv.innerHTML = results.map(result => `
                <div class="page">
                    <div class="page-number">
                        ${result.document_name} - Page ${result.page_number}
                    </div>
                    <div class="content">${result.content}</div>
                </div>
            `).join('');
        } catch (error) {
            contentDiv.innerHTML = `Error searching: ${error.message}`;
        }
    }
}

customElements.define('pdf-viewer', PdfViewer);
