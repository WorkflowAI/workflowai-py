from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import workflowai
from workflowai.core.domain.model import Model
from workflowai.fields import Image
import os
from dotenv import load_dotenv
from workflowai import Run, WorkflowAIError

# Load environment variables from .env file
load_dotenv()

class ImageInput(BaseModel):
    image: Image = Field(description="The image to analyze")

class ImageOutput(BaseModel):
    city: str = Field(default="", description="Name of the city shown in the image")
    country: str = Field(default="", description="Name of the country where the city is located")
    confidence: Optional[float] = Field(
        default=None, 
        description="Confidence level in the identification (0-1)"
    )

@workflowai.agent(id="city-identifier", model=Model.GEMINI_1_5_FLASH_LATEST)
async def identify_city_from_image(input: ImageInput) -> Run[ImageOutput]:
    """
    Analyze the provided image and identify the city and country shown in it.
    If the image shows a recognizable landmark or cityscape, identify the city and country.
    If uncertain, indicate lower confidence or leave fields empty.
    
    Focus on:
    - Famous landmarks
    - Distinctive architecture
    - Recognizable skylines
    - Cultural elements that identify the location
    
    Return empty strings if the city/country cannot be determined with reasonable confidence.
    """
    ...

async def run_city_identifier():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(current_dir, "assets", "new-york-city.jpg")
    
    with open(image_path, "rb") as image_file:
        import base64
        content = base64.b64encode(image_file.read()).decode("utf-8")
    
    image = Image(content_type='image/jpeg', data=content)
    try:
        agent_run = await identify_city_from_image(
            ImageInput(image=image),
            use_cache="auto"
        )
    except WorkflowAIError as e:
        print(f"Failed to run task. Code: {e.error.code}. Message: {e.error.message}")
        return

    print("\n--------\nAgent output:\n", agent_run.output, "\n--------\n")
    print(f"Cost: ${agent_run.cost_usd:.10f}")
    print(f"Latency: {agent_run.duration_seconds:.2f}s")

    # using URL for Image
    # TODO: replace with a Github URL
    image_url = "https://t4.ftcdn.net/jpg/02/96/15/35/360_F_296153501_B34baBHDkFXbl5RmzxpiOumF4LHGCvAE.jpg"
    image = Image(url=image_url)
    agent_run = await identify_city_from_image(
        ImageInput(image=image),
        use_cache="auto"
    )

    print("\n--------\nAgent output:\n", agent_run.output, "\n--------\n")
    print(f"Cost: ${agent_run.cost_usd:.10f}")
    print(f"Latency: {agent_run.duration_seconds:.2f}s")

if __name__ == "__main__":
    asyncio.run(run_city_identifier()) 
