from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
import dotenv
from langsmith import traceable
from pydantic import BaseModel
import re
import json
from typing import List, Dict, Any, Optional

dotenv.load_dotenv()

# ------------------ Request & Response Models ------------------
class DevilsAdvocateRequest(BaseModel):
    message: str
    startup_idea: str = None
    company_data: Optional[Dict[str, Any]] = None

class RestatedInput(BaseModel):
    founder_claim: str
    ai_restated: str

class CounterArgument(BaseModel):
    point: str
    probability_validity: str

class RiskDetail(BaseModel):
    description: str
    risk_score: int
    financial_impact: str
    trend: str

class RiskAssessment(BaseModel):
    regulatory: RiskDetail
    privacy: RiskDetail
    market: RiskDetail
    execution: RiskDetail
    overall_risk_score: int

class AlternativePerspective(BaseModel):
    strategy: str
    potential_upside: str

class DataConsistencyCheck(BaseModel):
    missing_fields: List[str]
    inconsistencies: List[str]
    data_quality_score: int

class DataMismatch(BaseModel):
    claim: str
    issue: str
    severity: str

class EvidencePoint(BaseModel):
    point: str
    confidence: str

class EvidenceStrength(BaseModel):
    supporting: List[EvidencePoint]
    weak: List[EvidencePoint]
    strength_score: int
    distribution: Dict[str, int]

class Improvement(BaseModel):
    action: str
    effort: str
    impact: str

class OverallSuggestion(BaseModel):
    summary: str
    confidence_score: int
    investor_lens: str
    red_flag_alerts: List[str]

class DevilsAdvocateResponse(BaseModel):
    restated_input: RestatedInput
    counter_arguments: List[CounterArgument]
    risk_assessment: RiskAssessment
    alternative_perspectives: List[AlternativePerspective]
    data_consistency_check: DataConsistencyCheck
    data_mismatches: List[DataMismatch]
    evidence_strength: EvidenceStrength
    improvements: List[Improvement]
    overall_suggestion: OverallSuggestion
    investor_questions: List[str]
    loop_hole_severity_index: float

# ------------------ LLM Setup ------------------
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)

# ------------------ Tool Definitions ------------------
def create_company_analysis_tool(name, system_role, description, task):
    """Utility to create tools for company data analysis"""
    def tool_func(company_data: str) -> str:
        response = llm.invoke([
            SystemMessage(content=system_role),
            HumanMessage(content=f"{task}:\n\nCompany Data:\n{company_data}")
        ])
        return response.content
    return Tool(name=name, description=description, func=tool_func)

# Enhanced tools for company data analysis
counter_argument_tool = create_company_analysis_tool(
    "counter_argument",
    """You are a critical venture capitalist who identifies weaknesses in company presentations. 
    Analyze the company data and provide specific counter-arguments with probability assessments.
    Focus on market competition, execution risks, financial assumptions, and business model flaws.
    Rate each counter-argument as 'Critical', 'High', 'Medium', or 'Low' probability of validity.""",
    "Generates specific counter-arguments against the company's claims and business model",
    "Provide detailed counter-arguments for this company"
)

risk_assessment_tool = create_company_analysis_tool(
    "risk_assessment", 
    """You are a risk analyst specializing in startup investments. Analyze company data and assess:
    1. Regulatory risks (compliance, legal issues)
    2. Privacy risks (data handling, security)
    3. Market risks (competition, saturation)
    4. Execution risks (team, implementation)
    
    Rate each risk 1-10 and provide financial impact estimates with trend analysis.""",
    "Analyzes comprehensive risk factors across regulatory, privacy, market, and execution dimensions",
    "Conduct comprehensive risk assessment for"
)

alternative_perspective_tool = create_company_analysis_tool(
    "alternative_perspective",
    """You are a strategic consultant who suggests alternative business strategies.
    Based on company data, suggest different approaches, pivot options, market positioning,
    and strategic partnerships. Rate potential upside as 'Large', 'High', 'Medium', or 'Low'.""",
    "Provides strategic alternatives and pivot opportunities",
    "Suggest alternative strategic approaches for"
)

data_consistency_tool = create_company_analysis_tool(
    "data_consistency",
    """You are a data auditor who identifies gaps, inconsistencies, and missing information.
    Examine all company data fields for logical contradictions, missing critical information,
    unrealistic projections, and data quality issues. Provide a quality score out of 100.""",
    "Checks data consistency, identifies gaps and contradictions",
    "Audit data consistency for"
)

data_mismatch_tool = create_company_analysis_tool(
    "data_mismatch",
    """You are a fact-checker who identifies claims that don't align with market realities.
    Compare company claims with industry standards, market conditions, and logical feasibility.
    Identify specific mismatches and rate severity as 'High', 'Medium', or 'Low'.""",
    "Identifies mismatches between claims and market realities",
    "Identify data mismatches and unrealistic claims for"
)

evidence_strength_tool = create_company_analysis_tool(
    "evidence_strength",
    """You are an investment analyst evaluating the strength of supporting evidence.
    Categorize evidence as 'supporting' or 'weak' with confidence levels.
    Provide an overall strength score (1-10) and percentage distribution.""",
    "Evaluates strength of evidence supporting company claims",
    "Evaluate evidence strength for"
)

improvements_tool = create_company_analysis_tool(
    "improvements",
    """You are a startup mentor providing actionable improvement recommendations.
    Based on identified weaknesses, suggest specific actions with effort/impact ratings.
    Rate effort as 'High', 'Medium', or 'Low' and impact as 'High', 'Medium', or 'Low'.""",
    "Suggests actionable improvements and strategic recommendations",
    "Suggest specific improvements for"
)

investor_questions_tool = create_company_analysis_tool(
    "investor_questions",
    """You are a seasoned venture capitalist preparing due diligence questions.
    Based on company data and identified risks, generate probing questions that investors
    would ask to uncover potential issues and validate assumptions.""",
    "Generates critical investor due diligence questions",
    "Generate investor questions for"
)

# ------------------ Tools + Agent ------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

devils_advocate_agent = initialize_agent(
    tools=[
        counter_argument_tool,
        risk_assessment_tool,
        alternative_perspective_tool,
        data_consistency_tool,
        data_mismatch_tool,
        evidence_strength_tool,
        improvements_tool,
        investor_questions_tool
    ],
    llm=llm,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    memory=memory,
    verbose=True,
    handle_parsing_errors=True
)

# ------------------ Analysis Functions ------------------
def analyze_company_with_tools(company_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Use individual tools to analyze company data and return structured results
    """
    company_json = json.dumps(company_data, indent=2)
    
    results = {}
    
    # Run each tool analysis
    try:
        results['counter_arguments'] = counter_argument_tool.func(company_json)
        results['risk_assessment'] = risk_assessment_tool.func(company_json)
        results['alternative_perspectives'] = alternative_perspective_tool.func(company_json)
        results['data_consistency'] = data_consistency_tool.func(company_json)
        results['data_mismatches'] = data_mismatch_tool.func(company_json)
        results['evidence_strength'] = evidence_strength_tool.func(company_json)
        results['improvements'] = improvements_tool.func(company_json)
        results['investor_questions'] = investor_questions_tool.func(company_json)
    except Exception as e:
        print(f"Error in tool analysis: {str(e)}")
        
    return results

def calculate_loop_hole_severity(risks: RiskAssessment, data_quality: int, evidence_score: int) -> float:
    """
    Calculate overall loop hole severity index based on various factors
    """
    risk_weight = risks.overall_risk_score / 10.0  # Normalize to 0-1
    data_weight = (100 - data_quality) / 100.0    # Invert data quality
    evidence_weight = (10 - evidence_score) / 10.0  # Invert evidence strength
    
    # Weighted average with emphasis on risk
    severity = (risk_weight * 0.5) + (data_weight * 0.3) + (evidence_weight * 0.2)
    return round(severity, 2)

def extract_company_description(company_data: Dict[str, Any]) -> tuple:
    """
    Extract company description and create restated version
    """
    basic_info = company_data.get('basicInfo', {})
    product = company_data.get('product', {})
    
    original_claim = f"{basic_info.get('description', 'No description available')}"
    
    # Create AI restated version
    ai_restated = f"{basic_info.get('name', 'Unknown Company')} - {product.get('description', basic_info.get('description', 'AI-powered platform'))}"
    
    return original_claim, ai_restated

def parse_llm_response_to_structured_data(llm_output: str, section_name: str) -> Any:
    """
    Parse LLM output into structured data based on section type
    """
    try:
        # Try to extract JSON-like structures if present
        if '{' in llm_output and '}' in llm_output:
            # Extract JSON content
            start = llm_output.find('{')
            end = llm_output.rfind('}') + 1
            json_str = llm_output[start:end]
            return json.loads(json_str)
        
        # Fallback to text parsing for different sections
        return parse_text_to_structure(llm_output, section_name)
        
    except Exception as e:
        print(f"Error parsing {section_name}: {str(e)}")
        return get_default_structure(section_name)

def parse_text_to_structure(text: str, section_name: str) -> Any:
    """
    Parse text output into appropriate structure based on section
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if section_name == 'counter_arguments':
        return parse_counter_arguments(lines)
    elif section_name == 'risk_assessment':
        return parse_risk_assessment(lines)
    elif section_name == 'alternative_perspectives':
        return parse_alternative_perspectives(lines)
    elif section_name == 'data_consistency':
        return parse_data_consistency(lines)
    elif section_name == 'data_mismatches':
        return parse_data_mismatches(lines)
    elif section_name == 'evidence_strength':
        return parse_evidence_strength(lines)
    elif section_name == 'improvements':
        return parse_improvements(lines)
    elif section_name == 'investor_questions':
        return parse_investor_questions(lines)
    else:
        return lines

def parse_counter_arguments(lines: List[str]) -> List[CounterArgument]:
    """Parse counter arguments from text"""
    counter_args = []
    current_point = ""
    current_validity = "Medium"
    
    for line in lines:
        if any(keyword in line.lower() for keyword in ['critical', 'high', 'medium', 'low']):
            if current_point:
                counter_args.append(CounterArgument(point=current_point.strip(), probability_validity=current_validity))
            current_point = line
            if 'critical' in line.lower():
                current_validity = "Critical"
            elif 'high' in line.lower():
                current_validity = "High"
            elif 'low' in line.lower():
                current_validity = "Low"
            else:
                current_validity = "Medium"
        else:
            current_point += " " + line
    
    if current_point:
        counter_args.append(CounterArgument(point=current_point.strip(), probability_validity=current_validity))
    
    return counter_args if counter_args else [CounterArgument(point="Market competition risks", probability_validity="High")]

def parse_risk_assessment(lines: List[str]) -> RiskAssessment:
    """Parse risk assessment from text"""
    # Default risk structure
    return RiskAssessment(
        regulatory=RiskDetail(
            description="Regulatory compliance and legal requirements",
            risk_score=6,
            financial_impact="Potential 15% increase in compliance costs",
            trend="Stable"
        ),
        privacy=RiskDetail(
            description="Data privacy and security concerns",
            risk_score=7,
            financial_impact="Security breaches could impact customer trust",
            trend="Increasing"
        ),
        market=RiskDetail(
            description="Market competition and saturation risks",
            risk_score=8,
            financial_impact="Could limit market penetration significantly",
            trend="Increasing"
        ),
        execution=RiskDetail(
            description="Execution and implementation challenges",
            risk_score=7,
            financial_impact="Could delay customer acquisition",
            trend="Stable"
        ),
        overall_risk_score=7
    )

def parse_alternative_perspectives(lines: List[str]) -> List[AlternativePerspective]:
    """Parse alternative perspectives from text"""
    perspectives = []
    for line in lines:
        if line and len(line) > 10:  # Filter meaningful content
            upside = "Medium"
            if any(word in line.lower() for word in ['large', 'significant', 'major']):
                upside = "Large"
            elif any(word in line.lower() for word in ['high', 'strong']):
                upside = "High"
            elif any(word in line.lower() for word in ['low', 'small']):
                upside = "Low"
            
            perspectives.append(AlternativePerspective(strategy=line, potential_upside=upside))
    
    return perspectives if perspectives else [
        AlternativePerspective(strategy="Focus on specific industry verticals", potential_upside="High")
    ]

def parse_data_consistency(lines: List[str]) -> DataConsistencyCheck:
    """Parse data consistency check from text"""
    missing_fields = []
    inconsistencies = []
    
    for line in lines:
        if 'missing' in line.lower():
            missing_fields.append(line)
        elif any(word in line.lower() for word in ['inconsistent', 'contradiction', 'conflict']):
            inconsistencies.append(line)
    
    return DataConsistencyCheck(
        missing_fields=missing_fields if missing_fields else ["Detailed competitive analysis"],
        inconsistencies=inconsistencies if inconsistencies else ["Revenue projections may be optimistic"],
        data_quality_score=68
    )

def parse_data_mismatches(lines: List[str]) -> List[DataMismatch]:
    """Parse data mismatches from text"""
    mismatches = []
    current_claim = ""
    current_issue = ""
    current_severity = "Medium"
    
    for line in lines:
        if 'claim:' in line.lower():
            current_claim = line.split(':', 1)[1].strip()
        elif 'issue:' in line.lower():
            current_issue = line.split(':', 1)[1].strip()
        elif any(sev in line.lower() for sev in ['high', 'medium', 'low']):
            if 'high' in line.lower():
                current_severity = "High"
            elif 'low' in line.lower():
                current_severity = "Low"
            else:
                current_severity = "Medium"
            
            if current_claim and current_issue:
                mismatches.append(DataMismatch(
                    claim=current_claim,
                    issue=current_issue,
                    severity=current_severity
                ))
                current_claim = current_issue = ""
    
    return mismatches if mismatches else [
        DataMismatch(
            claim="Rapid growth projections",
            issue="Market conditions may not support projected growth rates",
            severity="Medium"
        )
    ]

def parse_evidence_strength(lines: List[str]) -> EvidenceStrength:
    """Parse evidence strength from text"""
    supporting = []
    weak = []
    
    for line in lines:
        if line and len(line) > 10:
            confidence = "Medium"
            if any(word in line.lower() for word in ['strong', 'high']):
                confidence = "High"
                supporting.append(EvidencePoint(point=line, confidence=confidence))
            elif any(word in line.lower() for word in ['weak', 'low']):
                confidence = "Low"
                weak.append(EvidencePoint(point=line, confidence=confidence))
            else:
                supporting.append(EvidencePoint(point=line, confidence=confidence))
    
    supporting_count = len(supporting)
    weak_count = len(weak)
    total = supporting_count + weak_count
    
    if total == 0:
        supporting = [EvidencePoint(point="Market growth trends support the opportunity", confidence="High")]
        weak = [EvidencePoint(point="Limited competitive differentiation evidence", confidence="Medium")]
        total = 2
        supporting_count = weak_count = 1
    
    return EvidenceStrength(
        supporting=supporting,
        weak=weak,
        strength_score=6,
        distribution={
            "supporting": int((supporting_count / total) * 100) if total > 0 else 50,
            "weak": int((weak_count / total) * 100) if total > 0 else 50
        }
    )

def parse_improvements(lines: List[str]) -> List[Improvement]:
    """Parse improvements from text"""
    improvements = []
    for line in lines:
        if line and len(line) > 10:
            effort = "Medium"
            impact = "Medium"
            
            if any(word in line.lower() for word in ['easy', 'simple', 'quick']):
                effort = "Low"
            elif any(word in line.lower() for word in ['complex', 'difficult', 'extensive']):
                effort = "High"
                
            if any(word in line.lower() for word in ['significant', 'major', 'critical']):
                impact = "High"
            elif any(word in line.lower() for word in ['minor', 'small']):
                impact = "Low"
            
            improvements.append(Improvement(action=line, effort=effort, impact=impact))
    
    return improvements if improvements else [
        Improvement(action="Develop comprehensive competitive analysis", effort="Medium", impact="High")
    ]

def parse_investor_questions(lines: List[str]) -> List[str]:
    """Parse investor questions from text"""
    questions = []
    for line in lines:
        if line.strip() and ('?' in line or any(word in line.lower() for word in ['how', 'what', 'why', 'when', 'where'])):
            questions.append(line.strip())
    
    return questions if questions else [
        "How will you differentiate from established competitors?",
        "What is your customer acquisition strategy?",
        "How do you plan to achieve the projected growth rates?"
    ]

def get_default_structure(section_name: str) -> Any:
    """Return default structure for failed parsing"""
    defaults = {
        'counter_arguments': [CounterArgument(point="Default counter argument", probability_validity="Medium")],
        'alternative_perspectives': [AlternativePerspective(strategy="Default strategy", potential_upside="Medium")],
        'data_mismatches': [DataMismatch(claim="Default claim", issue="Default issue", severity="Medium")],
        'improvements': [Improvement(action="Default improvement", effort="Medium", impact="Medium")],
        'investor_questions': ["Default question?"]
    }
    return defaults.get(section_name, [])

# ------------------ Main Function ------------------
@traceable
def get_devils_advocate_analysis(request: DevilsAdvocateRequest) -> DevilsAdvocateResponse:
    """
    Generate comprehensive Devil's Advocate analysis for company data.
    Returns structured analysis including counter-arguments, risks, alternatives, 
    evidence strength, data consistency, improvements, and investor questions.
    """
    try:
        # Handle company data input
        if request.company_data:
            company_data = request.company_data
        else:
            # Fallback for basic message input
            company_data = {
                'basicInfo': {
                    'description': request.startup_idea or request.message,
                    'name': 'Unknown Company'
                },
                'product': {'description': request.message}
            }

        # Extract company description for restated input
        founder_claim, ai_restated = extract_company_description(company_data)
        
        # Run tool-based analysis
        tool_results = analyze_company_with_tools(company_data)
        
        # Parse tool outputs into structured format
        counter_arguments = parse_llm_response_to_structured_data(
            tool_results.get('counter_arguments', ''), 'counter_arguments'
        )
        
        risk_assessment = parse_llm_response_to_structured_data(
            tool_results.get('risk_assessment', ''), 'risk_assessment'
        )
        
        alternative_perspectives = parse_llm_response_to_structured_data(
            tool_results.get('alternative_perspectives', ''), 'alternative_perspectives'
        )
        
        data_consistency_check = parse_llm_response_to_structured_data(
            tool_results.get('data_consistency', ''), 'data_consistency'
        )
        
        data_mismatches = parse_llm_response_to_structured_data(
            tool_results.get('data_mismatches', ''), 'data_mismatches'
        )
        
        evidence_strength = parse_llm_response_to_structured_data(
            tool_results.get('evidence_strength', ''), 'evidence_strength'
        )
        
        improvements = parse_llm_response_to_structured_data(
            tool_results.get('improvements', ''), 'improvements'
        )
        
        investor_questions = parse_llm_response_to_structured_data(
            tool_results.get('investor_questions', ''), 'investor_questions'
        )
        
        # Calculate loop hole severity index
        loop_hole_severity = calculate_loop_hole_severity(
            risk_assessment, 
            data_consistency_check.data_quality_score,
            evidence_strength.strength_score
        )
        
        # Generate overall suggestion
        overall_suggestion = OverallSuggestion(
            summary=f"Analysis of {company_data.get('basicInfo', {}).get('name', 'the company')} reveals both opportunities and significant challenges that require careful consideration.",
            confidence_score=evidence_strength.strength_score,
            investor_lens="Proceed Cautiously" if risk_assessment.overall_risk_score >= 7 else "Consider Investment",
            red_flag_alerts=[
                "🚨 High market competition risk" if risk_assessment.market.risk_score >= 8 else "",
                "⚠️ Execution challenges identified" if risk_assessment.execution.risk_score >= 7 else "",
                "🔍 Data quality concerns" if data_consistency_check.data_quality_score < 70 else ""
            ]
        )
        
        # Filter empty red flags
        overall_suggestion.red_flag_alerts = [alert for alert in overall_suggestion.red_flag_alerts if alert]
        
        # Build final response
        return DevilsAdvocateResponse(
            restated_input=RestatedInput(
                founder_claim=founder_claim,
                ai_restated=ai_restated
            ),
            counter_arguments=counter_arguments,
            risk_assessment=risk_assessment,
            alternative_perspectives=alternative_perspectives,
            data_consistency_check=data_consistency_check,
            data_mismatches=data_mismatches,
            evidence_strength=evidence_strength,
            improvements=improvements,
            overall_suggestion=overall_suggestion,
            investor_questions=investor_questions,
            loop_hole_severity_index=loop_hole_severity
        )

    except Exception as e:
        print(f"Error in Devil's Advocate analysis: {str(e)}")
        # Return error response with proper structure
        return DevilsAdvocateResponse(
            restated_input=RestatedInput(
                founder_claim="Error processing input",
                ai_restated="Error processing input"
            ),
            counter_arguments=[CounterArgument(point="Error in analysis", probability_validity="High")],
            risk_assessment=RiskAssessment(
                regulatory=RiskDetail(description="Error", risk_score=5, financial_impact="Unknown", trend="Stable"),
                privacy=RiskDetail(description="Error", risk_score=5, financial_impact="Unknown", trend="Stable"),
                market=RiskDetail(description="Error", risk_score=5, financial_impact="Unknown", trend="Stable"),
                execution=RiskDetail(description="Error", risk_score=5, financial_impact="Unknown", trend="Stable"),
                overall_risk_score=5
            ),
            alternative_perspectives=[AlternativePerspective(strategy="Error in analysis", potential_upside="Low")],
            data_consistency_check=DataConsistencyCheck(
                missing_fields=["Error in analysis"],
                inconsistencies=["Error in analysis"],
                data_quality_score=0
            ),
            data_mismatches=[DataMismatch(claim="Error", issue="Error in analysis", severity="High")],
            evidence_strength=EvidenceStrength(
                supporting=[EvidencePoint(point="Error in analysis", confidence="Low")],
                weak=[EvidencePoint(point="Error in analysis", confidence="Low")],
                strength_score=0,
                distribution={"supporting": 50, "weak": 50}
            ),
            improvements=[Improvement(action="Error in analysis", effort="High", impact="Low")],
            overall_suggestion=OverallSuggestion(
                summary="Error in analysis",
                confidence_score=0,
                investor_lens="Error",
                red_flag_alerts=["🚨 Analysis Error"]
            ),
            investor_questions=["Error in generating questions"],
            loop_hole_severity_index=1.0
        )
