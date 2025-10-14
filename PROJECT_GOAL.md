# Hotel Sales AI Agent - Project Goal

## Overview

An intelligent AI agent system designed to assist hotel guests in booking their stay through natural conversation. The agent understands complex booking requirements, queries hotel availability through PMS APIs, and generates booking links based on guest preferences.

## Core Objectives

### 1. Intelligent Conversation Management
The AI agent must be capable of understanding diverse guest requirements through natural language, including:

- **Complex family bookings**: Multiple families with varying children counts (e.g., 2 families: one with 2 kids, another with 1 kid)
- **Flexible date requests**: Approximate timeframes like "Christmas period" or "end of next month"
- **Simple bookings**: Couples for weekends, single travelers, specific dates
- **Iterative refinement**: Guests can change their minds and modify requirements mid-conversation

### 2. Intent Understanding & API Orchestration

The agent must:
- **Extract intent** from guest messages to determine which operation to perform
- **Identify required information** and ask relevant questions when data is missing
- **Distinguish between static and dynamic data** to optimize API calls vs. cache usage
- **Call appropriate PMS APIs** with correctly formatted parameters
- **Return structured results** to guests in a clear, conversational manner

### 3. Dynamic Data Processing

**Critical Rule**: The AI model must NEVER generate or hallucinate prices.
- Price information and availability must come exclusively from API responses
- The model should use placeholders for prices during composition
- Placeholders are replaced with actual API data before presenting to the guest

### 4. Booking Link Generation

The final output of successful conversations should be:
- A valid booking link generated based on all gathered requirements
- The link should direct to the hotel's booking system with pre-filled parameters

## Architectural Principles

### PMS Agnostic Design
- **Abstraction layer**: The system must support any Property Management System (PMS)
- **Object-oriented architecture**: Clean separation between business logic and PMS-specific implementations
- **Initial implementation**: Start with MiniHotel PMS (documentation in `minihotel-api-docs.md`)
- **Future extensibility**: Easy addition of new PMS integrations through well-defined interfaces

### Performance Optimization
- **Parallel processing** for intent detection and data retrieval:
  - Run intent understanding to determine which agent/workflow to trigger
  - Simultaneously fetch commonly needed data (e.g., room types, base availability)
  - Balance parallelism with avoiding unnecessary API calls

### AI Integration
- **OpenAI models** for:
  - Natural language understanding
  - Intent extraction
  - Context and date parsing
  - Response generation
- **Structured outputs** for API parameter extraction
- **Conversational flow** management across multi-turn interactions

## Testing Strategy

### Conversation Examples as Test Cases
- Example conversations are stored in `chat_conversations.md`
- Each conversation represents a target behavior pattern
- Every conversation should eventually become an automated test case
- Tests validate:
  - Correct intent detection
  - Appropriate API calls with correct parameters
  - Accurate information extraction
  - Proper handling of requirement changes
  - Valid booking link generation

## Success Criteria

A successful implementation will:

1. Handle all conversation patterns documented in `chat_conversations.md`
2. Never hallucinate prices or availability data
3. Ask clarifying questions when information is missing
4. Support iterative requirement refinement
5. Generate valid booking links for confirmed requirements
6. Work seamlessly with MiniHotel PMS
7. Provide clear extension points for additional PMS integrations
8. Pass all test cases derived from example conversations

## Technology Stack

- **AI/ML**: OpenAI API for language understanding and generation
- **Architecture**: Object-oriented Python with PMS abstraction layer
- **Initial PMS**: MiniHotel API
- **Testing**: Conversation-driven test cases

## Development Phases

### Phase 1: Foundation
- PMS abstraction layer design
- MiniHotel integration
- Basic intent detection
- Simple conversation flow

### Phase 2: Intelligence
- Advanced intent understanding
- Parallel API optimization
- Context extraction (dates, guests, rooms)
- Requirement modification handling

### Phase 3: Production Ready
- Comprehensive test suite from conversation examples
- Booking link generation
- Error handling and edge cases
- Performance optimization

### Phase 4: Expansion
- Additional PMS integrations
- Advanced features (upselling, recommendations)
- Analytics and monitoring
