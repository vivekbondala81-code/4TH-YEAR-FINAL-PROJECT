# Autonomous Data Analyst

An AI-powered autonomous data analysis system that performs hypothesis-driven investigation of datasets with complete traceability and verification.

## Features

- **Dataset Profiling**: Automatic analysis of dataset structure, types, missing values, and quality
- **Data Quality Reports**: Comprehensive quality assessment with recommendations
- **Analysis Planning**: AI-driven planning that converts goals into executable steps
- **Hypothesis Generation**: Multiple hypothesis generation and testing
- **Tool Execution**: Python (Pandas, NumPy, SciPy, scikit-learn), SQL, and statistical analysis
- **Verification Engine**: Cross-checks results for consistency and reliability
- **Evidence Store**: Complete traceability of all analysis steps
- **Real-time Dashboard**: Interactive Next.js frontend with live progress updates
- **Visualization**: Automatic chart generation using Plotly
- **General Question Answering**: AI-powered answers to general business/analytical questions
- **Multi-Format Export**: Export datasets and results in CSV, Excel, or JSON formats
- **Dimension Comparison**: Compare different dimensions in your dataset
- **Advanced Filtering**: Filter data using various operators (equals, contains, greater than, etc.)
- **Automatic Type Detection**: Smart conversion of string columns to numeric when appropriate
- **Universal Data Support**: Works with numeric, categorical, and mixed datasets

## Architecture

```
User → Next.js Dashboard → FastAPI Backend → Analysis Pipeline
                                         ↓
                                Dataset Profiler
                                         ↓
                                Analysis Planner
                                         ↓
                              Hypothesis Engine
                                         ↓
                            Tool Execution Layer
                                         ↓
                              Evidence Store
                                         ↓
                            Verification Engine
                                         ↓
                           Report Generator
```

## Technology Stack

### Backend
- FastAPI (Python web framework)
- Pandas / Polars (Data manipulation)
- SciPy (Statistical analysis)
- scikit-learn (Machine learning)
- Plotly (Visualization)
- SQLAlchemy (Database operations)
- WebSockets (Real-time updates)
- **Google Gemini AI** (LLM-powered analysis planning and interpretation)
- **LangGraph** (Agentic workflow orchestration)

### Frontend
- Next.js 14 (React framework)
- TypeScript
- Tailwind CSS
- Plotly.js (Interactive charts)
- Axios (HTTP client)

## Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- Git

### Quick Start (Windows)

```bash
# 1. Set up API keys (required for AI features)
# Copy backend/.env.example to backend/.env
# Add your Gemini API keys to backend/.env

# 2. Terminal 1 - Start Backend
start-backend.bat

# 3. Terminal 2 - Start Frontend
start-frontend.bat
```

### Manual Setup

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Usage

1. **Upload Dataset**: Upload a CSV or Excel file through the dashboard
2. **Review Profile**: Examine the automatically generated dataset profile and quality report
3. **Define Goal**: Enter your analysis goal in natural language (e.g., "Analyze why sales decreased in some regions")
4. **Start Analysis**: The system will:
   - Create an analysis plan
   - Generate multiple hypotheses
   - Execute appropriate tools
   - Detect anomalies
   - Generate visualizations
   - Verify results
   - Create a comprehensive report

5. **Review Results**: Explore the analysis plan, hypotheses, evidence, visualizations, and final report

## Sample Dataset

A sample sales dataset is provided in `sample-data/sales.csv` for testing.

## API Endpoints

- `POST /upload` - Upload dataset
- `POST /analyze` - Start analysis with goal
- `POST /execute` - Execute analysis plan
- `POST /verify` - Verify analysis results
- `POST /report` - Generate final report
- `GET /session/{session_id}` - Get session state
- `GET /report/{session_id}/download` - Download report (HTML or JSON)
- `POST /export` - Export dataset in CSV, Excel, or JSON format
- `POST /compare` - Compare different dimensions in the dataset
- `POST /filter` - Filter dataset based on criteria
- `WS /ws/{session_id}` - WebSocket for real-time updates

## Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── analysis/              # Analysis modules
│   │   ├── dataset_profiler.py
│   │   ├── data_quality.py
│   │   ├── analysis_planner.py
│   │   ├── hypothesis_engine.py
│   │   ├── tool_executor.py
│   │   ├── verification_engine.py
│   │   ├── evidence_store.py
│   │   ├── analysis_memory.py
│   │   └── report_generator.py
│   └── websocket/             # WebSocket manager
│       └── connection_manager.py
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js app
│   │   ├── components/       # React components
│   │   └── lib/              # Utilities
│   ├── package.json
│   └── tsconfig.json
├── sample-data/
│   └── sales.csv             # Sample dataset
└── README.md
```

## Key Features Explained

### AI-Powered Analysis with Gemini
- **LLM-Driven Planning**: Uses Google Gemini AI to generate intelligent analysis plans based on natural language goals
- **Smart Hypothesis Generation**: AI generates multiple testable hypotheses automatically
- **Intelligent Tool Selection**: LLM selects the best tools for each hypothesis
- **Result Interpretation**: AI interprets statistical results and provides actionable insights
- **Natural Language Understanding**: Users can describe goals in plain English

### Hypothesis-Driven Analysis
Unlike simple AI analytics, this system generates multiple hypotheses and tests each one independently, avoiding premature conclusions.

### Evidence Traceability
Every conclusion can be traced back to specific tool executions, calculations, and verification steps.

### Verification Layer
Results are cross-checked using alternative methods, statistical validation, and consistency checks before being accepted.

### Revision Loop
If verification fails, the system automatically revises the analysis and re-executes.

### Real-Time Progress
WebSocket connections provide live updates of analysis progress to the dashboard.

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
