# Insurance Claim Validator Backend

AI-powered insurance claim validation system that automatically validates car insurance claims by extracting data from documents, validating consistency, and analyzing damage images.

## Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account (or local MongoDB instance)
- Groq API key

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd insurance-claim-validator-backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   # MongoDB Configuration
   ATLAS_URL=mongodb+srv://username:password@cluster.mongodb.net/
   DB_NAME=dev

   # Groq API Configuration
   GROQ_API_KEY=your_groq_api_key_here

   # Application Configuration (optional)
   VERSION=1.0.0
   BUILD=dev
   ```

## Running the Application

### Development Mode

Run the application using uvicorn:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 4111 --reload
```

Or directly:

```bash
python app/main.py
```

The API will be available at:
- **API**: http://localhost:4111
- **Swagger UI**: http://localhost:4111/swagger
- **ReDoc**: http://localhost:4111/api-redoc

### Using Docker

1. **Build the Docker image**
   ```bash
   docker build -t insurance-claim-validator .
   ```

2. **Run the container**
   ```bash
   docker run -p 80:80 --env-file .env insurance-claim-validator
   ```

## API Endpoints

### Health Check
- `GET /` - Welcome message with API information
- `GET /health` - Health check endpoint with database status

### Claims Management

- `POST /api/v1/claims/create` - Create a new claim
- `GET /api/v1/claims/` - Get all claims (with pagination)
- `GET /api/v1/claims/{claim_id}` - Get claim details by ID
- `POST /api/v1/claims/{claim_id}/documents` - Upload a document
- `POST /api/v1/claims/{claim_id}/images` - Upload a damage image
- `POST /api/v1/claims/{claim_id}/validate` - Validate a claim

### Document Types

Supported document types for upload:
- `policy` - Insurance policy document
- `claim_form` - Claim form document
- `driving_license` - Driving license
- `aadhaar` - Aadhaar card
- `pan` - PAN card
- `repair_estimate` - Repair estimate document

