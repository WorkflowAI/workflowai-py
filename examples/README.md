# WorkflowAI Examples

This directory contains example agents demonstrating different capabilities of the WorkflowAI SDK.

## Image Analysis Examples

### City Identifier
[city_identifier.py](./images/city_identifier.py)

An agent that identifies cities from images. Given a photo of a city, it:
- Identifies the city and country
- Explains the reasoning behind the identification
- Lists key landmarks or architectural features visible in the image
- Provides confidence level in the identification

Uses the `Image` field type to handle image inputs and Claude 3.5 Sonnet for its strong visual analysis capabilities.

## Document Analysis Examples

### PDF Question Answering
[pdf_answer.py](./pdf_answer.py)

An agent that answers questions about PDF documents. Given a PDF and a question, it:
- Analyzes the PDF content
- Provides a clear and concise answer to the question
- Includes relevant quotes from the document to support its answer

Uses the `File` field type to handle PDF inputs and Claude 3.5 Sonnet for its strong document comprehension abilities.

## Workflow Pattern Examples

For examples of different workflow patterns (chains, routing, parallel processing, etc.), see the [workflows](./workflows) directory. 