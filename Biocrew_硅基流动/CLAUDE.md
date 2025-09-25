# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent system built with the CrewAI framework for wastewater microbial purification technology development and optimization. The system implements a complete automated workflow through 6 AI agents collaborating to "screen functional microorganisms → design microbial agents → evaluate effectiveness → generate implementation plans". 

Note: The core algorithms (Tool_api, Tool_Carveme, ctFBA, and evaluation formulas) are currently only described in the agent backstories and task descriptions, with actual implementation pending as indicated by TODO comments throughout the codebase.

## Codebase Architecture

The system follows a two-layer architecture with 6 types of agents:

### Functional Execution Layer (4 core agents)
1. **Engineering Microorganism Identification Agent** - Screens functional microorganisms and metabolically complementary microorganisms based on water purification goals
2. **Microbial Agent Design Agent** - Designs microbial agents using ctFBA (cooperative trade-off metabolic flux balance) method
3. **Microbial Agent Evaluation Agent** - Evaluates biological purification effectiveness and community ecological characteristics
4. **Implementation Plan Generation Agent** - Generates complete microbial purification technology implementation plans

### Support Service Layer (2 agents)
5. **Knowledge Management Agent** - Acquires, stores, and provides domain knowledge
6. **Task Coordination Agent** - Controls workflow execution order and handles multi-objective and exception situations

## Common Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Then edit .env with your API keys
```

### Running the Application
```bash
# Run the main application
python3 main.py
```

### Code Validation
```bash
# Check for syntax errors
python3 -m py_compile main.py

# Check all Python files for syntax errors
find . -name "*.py" -exec python3 -m py_compile {} \;
```

### Git Operations
When pushing changes, make sure to push to both repositories:
```bash
# Push to organization repository
git push upstream master

# Push to personal repository
git push origin master
```

## Project Structure
```
BioCrew/
├── main.py                 # Main entry point (fully implemented)
├── requirements.txt        # Project dependencies
├── .env.example           # Environment variable configuration example
├── CLAUDE.md              # Claude Code development guide
├── DOCS/                  # Detailed documentation
│   ├── AGENTS.md          # Agent detailed documentation
│   ├── TOOLS.md           # Tool detailed documentation
│   ├── TASKS.md           # Task detailed documentation
│   └── TESTS.md           # Test detailed documentation
├── tests/                 # Test files
│   ├── test_Agent_Search.py               # Agent search test
│   └── test_database_query_user_input.py  # Database query test with user input
├── config/
│   └── config.py          # Configuration file (fully implemented)
├── agents/                # Agent definitions (fully implemented with TODOs for core algorithms)
│   ├── task_coordination_agent.py              # Task coordination agent
│   ├── engineering_microorganism_identification_agent.py  # Engineering microorganism identification agent
│   ├── microbial_agent_design_agent.py         # Microbial agent design agent
│   ├── microbial_agent_evaluation_agent.py     # Microbial agent evaluation agent
│   ├── implementation_plan_generation_agent.py  # Implementation plan generation agent
│   └── knowledge_management_agent.py           # Knowledge management agent
├── tasks/                 # Task definitions (fully implemented with TODOs for core algorithms)
│   ├── microorganism_identification_task.py    # Microorganism identification task
│   ├── microbial_agent_design_task.py          # Microbial agent design task
│   ├── microbial_agent_evaluation_task.py      # Microbial agent evaluation task
│   ├── implementation_plan_generation_task.py  # Implementation plan generation task
│   └── task_coordination_task.py               # Task coordination task
├── tools/                 # Custom tools (partially implemented)
│   ├── evaluation_tool.py
│   ├── database_tool_factory.py           # Factory for creating database tools
│   ├── pollutant_data_query_tool.py       # Query all data for a specific pollutant
│   ├── gene_data_query_tool.py            # Query gene data for a specific pollutant
│   ├── organism_data_query_tool.py        # Query organism data for a specific pollutant
│   ├── pollutant_summary_tool.py          # Get summary statistics for a specific pollutant
│   ├── pollutant_search_tool.py           # Search pollutants by keyword
│   ├── pollutant_name_utils.py            # Utility functions for pollutant name standardization
│   ├── envipath_tool.py                  # EnviPath database access tool
│   └── kegg_tool.py                      # KEGG database access tool
└── models/                # Model configurations (to be completed)
```

## Key Implementation Details

### Data Flow
- Knowledge Management → Functional Execution Layer agents
- Previous agent output → Next agent input
- Feedback loop: Evaluation failure → Update prompts → Re-identify microorganisms

### Core Algorithms (Partially implemented, with TODOs)
1. **Tool_api and Tool_Carveme** - For retrieving genomic/enzyme sequence data and converting genomes to metabolic models
   - Currently only described in agent backstories, actual implementation pending
2. **ctFBA algorithm** - Cooperative trade-off metabolic flux balance method for metabolic flux calculations
   - Currently only described in agent backstories, actual implementation pending
3. **Evaluation formulas** - Including competition index, complementarity index, Pianka niche overlap index, species knockout index
   - Currently only described in agent backstories, actual implementation pending

### Configuration
The system supports both DashScope (Qwen) and OpenAI model configurations through environment variables in the `.env` file.

### Specialized Data Access
The system now uses specialized database tools that replace the previous monolithic UnifiedDataTool, providing focused interfaces for different data access needs:

1. **PollutantDataQueryTool** - Query all data for a specific pollutant
2. **GeneDataQueryTool** - Query gene data for a specific pollutant
3. **OrganismDataQueryTool** - Query organism data for a specific pollutant
4. **PollutantSummaryTool** - Get summary statistics for a specific pollutant
5. **PollutantSearchTool** - Search pollutants by keyword

These tools are managed by the DatabaseToolFactory for easy instantiation and use.

### Pollutant Name Standardization
A new utility module `pollutant_name_utils.py` has been added to handle pollutant name standardization:
- Standardizes different formats of pollutant names to a consistent format for database queries
- Generates multiple name variants for improved search and matching
- Handles Greek letters, abbreviations, and special characters

### External Database Access Tools

The system integrates with external databases through the following tools:

1. **EnviPathTool** - Accesses environmental contaminant biotransformation pathway data from the enviPath database
   - `_run(operation, **kwargs)` - Unified interface for all EnviPath operations
   - Operations: `search_compound`, `get_pathway_info`, `get_compound_pathways`, `search_pathways_by_keyword`
   - Also supports direct method calls: `search_compound(compound_name)`, `get_pathway_info(pathway_id)`, etc.

2. **KeggTool** - Accesses biological pathway and genomic data from the KEGG database
   - `_run(operation, **kwargs)` - Unified interface for all KEGG operations
   - Operations: `get_database_info`, `list_entries`, `find_entries`, `get_entry`, `link_entries`, `convert_id`, `search_pathway_by_compound`, `search_genes_by_pathway`, `search_enzymes_by_compound`
   - Also supports direct method calls for each operation

### Evaluation Tool

3. **EvaluationTool** - Analyzes and evaluates microbial agent effectiveness
   - `_run(operation, **kwargs)` - Unified interface for evaluation operations
   - Operations: `analyze_evaluation_result`, `check_core_standards`
   - Also supports direct method calls: `analyze_evaluation_result(evaluation_report)`, `check_core_standards(evaluation_report)`

## Development Guidelines

### Code Organization
- Each agent is defined in its own file in the `agents/` directory
- Each task is defined in its own file in the `tasks/` directory
- Shared functionality should be implemented in the `tools/` directory
- Configuration is managed through the `config/` directory
- Local data is stored in the `data/` directory

### Tool Structure
All tools follow a consistent pattern:
1. Each tool inherits from `crewai.tools.BaseTool` for CrewAI compatibility
2. Each tool has a dedicated Pydantic model for input parameters (args_schema)
3. Tools implement a `_run()` method with explicit parameter definitions
4. Tools use `object.__setattr__` and `object.__getattribute__` to handle instance attributes and avoid Pydantic validation issues
5. Tools return consistent result formats with `status`, `data`, and error information

### Tool Factory Pattern
Database tools are managed through the DatabaseToolFactory:
1. Provides a centralized way to create all database tools
2. Allows easy instantiation of individual tools by name
3. Ensures consistent tool initialization across the application

### Agent Structure
Agents follow a consistent pattern:
1. Each agent is implemented as a class with a `create_agent()` method
2. The `create_agent()` method returns a configured CrewAI Agent instance
3. Agents define their role, goal, and backstory
4. Agents can use custom tools for specialized functionality

### Task Structure
Tasks follow a consistent pattern:
1. Each task is implemented as a class with a `create_task()` method
2. The `create_task()` method returns a configured CrewAI Task instance
3. Tasks define their description and expected output
4. Tasks can depend on other tasks through the context parameter

### Adding New Features
1. To add a new agent, create a new file in the `agents/` directory following the existing pattern
2. To add a new task, create a new file in the `tasks/` directory following the existing pattern
3. Register new agents and tasks in `main.py`
4. Update the Crew configuration in `main.py` to include new agents and tasks
5. For data access functionality, implement new tools in the `tools/` directory

## Recent Architecture Optimization

The system has undergone significant optimization to simplify the architecture and improve maintainability:

### Tool Specialization
- Replaced the legacy monolithic UnifiedDataTool with specialized database tools
- Each tool now has a specific responsibility, improving clarity and maintainability
- This includes:
  - PollutantDataQueryTool
  - GeneDataQueryTool
  - OrganismDataQueryTool
  - PollutantSummaryTool
  - PollutantSearchTool

### Agent Backstory Simplification
- Significantly reduced the length and complexity of agent backstories
- Streamlined tool usage instructions
- Improved clarity and focus on core functionality

### Benefits of Optimization
1. **Improved Clarity**: Each tool has a specific, well-defined purpose
2. **Better Maintainability**: Easier to update and extend individual tools
3. **Enhanced Reliability**: Reduced potential for tool coordination issues
4. **Easier Debugging**: Issues can be isolated to specific tools
5. **Better Performance**: Tools are optimized for their specific functions

## Recent Enhancements

### Natural Language Processing Improvements
- Enhanced pollutant recognition and translation capabilities in the Engineering Microorganism Identification Agent
- Added support for automatic translation of natural language pollutant descriptions to standard scientific terms
- Improved tool calling functionality with better error handling and data completeness assessment

### Dynamic Workflow Implementation
- Implemented a dynamic workflow in main.py that can re-execute tasks based on evaluation results
- Added feedback loops for continuous improvement of microbial identification and design
- Implemented maximum iteration limits to prevent infinite loops

### User Input Support
- Added support for user-defined water treatment requirements in the main application
- Created test scripts that allow users to input custom pollutant names for database queries
- Improved the user experience with clear prompts and instructions

### Database Query Enhancements
- Enhanced database tools with better error handling and data validation
- Added pollutant name standardization utilities for improved database query accuracy
- Implemented more robust database connection management