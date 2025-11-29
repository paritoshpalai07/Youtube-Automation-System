from dotenv import load_dotenv
from google import genai
from murf import Murf
from moviepy import VideoFileClip, TextClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip,ColorClip
import os
import json
import datetime
import requests
import logging
from pathlib import Path
from schedule import every, repeat, run_pending
from time import sleep
import shutil 
import yt_upload

project_dir = Path.home() / "Desktop" / "Youtube Automation"
load_dotenv(f"{project_dir / ".env"}")

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@repeat(every().day.at("08:00"))
@repeat(every().day.at("20:00"))
def yt_automation():
    riddle_file_path = project_dir / "riddles.txt"

    try:
        client = genai.Client(api_key=os.getenv("Gemini_Api"))
        exisiting_riddles = ""
        
        with open(riddle_file_path, "r") as f:
            exisiting_riddles = f.read()

        riddle_prompt = f"""
        Generate a highly engaging riddle for a YouTube Shorts video.
        Follow these strict requirements:
        The output must be in JSON format with the following keys, in this exact order:
        "intro-commentary" - a friendly, energetic intro line to start the Short (e.g., “Alright smarty brains, let's see how fast you can solve this one!”).
        "hook" - an attention-grabbing line (e.g., “Only geniuses can crack this riddle…”).
        "riddle" - a short, clever riddle solvable in 20-30 seconds.
        "commentary" - playful suspense-building statements.
        "call-to-action" - a line encouraging viewers to comment their answer.
        "answer-commentary" - a teasing line before revealing the answer.
        "answer" - the final correct answer (e.g. the correct answer is).
        Make the tone fun, engaging, and suitable for YouTube Shorts.
        Keep the sentences short and high-energy.
        The riddle must be original and spark curiosity.
        DO NOT add anything outside the JSON.
        and it should not be in the following list: {exisiting_riddles}
        """

        logger.info("Requesting riddle to Gemini...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=riddle_prompt,
        )

        riddle = json.loads(response.text.replace("```","").replace("json",""))
        logger.info("Response from Gemini has been received")

        riddle_answer = riddle["answer"]
        riddle_text = riddle["riddle"]
        riddle_text = riddle_text.replace(". ",".\n")

        riddle_str = ""
        for key in riddle:
            riddle_str += riddle[key] + " "

        prompt = f"based on the following write me a only one title for the youtube shorts video nothing else: '{riddle_str}'"

        logger.info("Generating video title...")

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        youtube_title = response.text

        logger.info("Video title generated successfully")
        logger.info("Generating Video Tags...")

        prompt = f"based on the following give me a python list of youtube shorts video tags for the youtube shorts video, DO NOT add anything outside than python list: '{riddle_str}'"

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        youtube_tags = response.text.replace("'''","").replace("python","").strip("[]").replace("'","").replace('"',"").split(",")
        youtube_tags = [tags.strip() for tags in youtube_tags]
        logger.info("Youtube video tags generated successfully")

        logger.info("Adding riddle to riddle list...")
        with open(riddle_file_path, "a") as f:
            f.write(riddle["answer"])
            f.write("\n")
        logger.info("Successfully added riddle to existing riddle list")

        client = Murf(
            api_key=os.getenv("Murf_Api")
        )

        logger.info("Creating folder for video...")
        folder_name = f"{datetime.date.today()} {riddle["answer"]}"
        folder_path = project_dir / "Generated Videos" / folder_name
        os.mkdir(folder_path)
        os.chdir(folder_path)
        logger.info("Folder created successfully!")
        logger.info("Generating audio for the video...")

        script_path = Path(folder_path) / "script.mp3"
        bg_music_path = project_dir / "Musics" / "bgmusic1.mp3"
        video_clip_path = project_dir / "Resources" / "character_edited.mp4"
        font_file_path = project_dir / "fonts" / "Permanent_Marker" / "PermanentMarker-Regular.ttf"

        res = client.text_to_speech.generate(
                text=riddle_str,
                # voice_id="en-US-terrell",
                voice_id="en-US-ken",
            )

        response = requests.get(res.audio_file)

        with open(script_path, "wb") as f:
            f.write(response.content)

        logger.info("Successfully generated audio file")
        logger.info("Merging video and audio...")
        
        script = AudioFileClip(script_path)
        script_duration = script.duration
        bg_music = AudioFileClip(bg_music_path).with_volume_scaled(0.05).with_duration(script_duration)
        final_audio = CompositeAudioClip([script, bg_music])

        video_clip = VideoFileClip(video_clip_path).with_duration(script_duration)

        final_video = video_clip.with_audio(final_audio)

        text = TextClip(text=f"{riddle_text}", font=font_file_path, font_size=50, color="white",size=(940, 480), method='caption', text_align="center")
        text = text.with_position(("center",1340))
        text = text.with_duration(script_duration)

        shadow = TextClip(text=f"{riddle_text}", font=font_file_path, font_size=50, color="black", size=(940, 480), method='caption', text_align="center")
        shadow = shadow.with_position(("center", 1345))
        shadow = shadow.with_opacity(0.2)
        shadow = shadow.with_duration(script_duration)

        bg = ColorClip(size=(text.w+40, text.h), color=(229, 56, 59))
        bg = bg.with_position(("center",1340))
        bg = bg.with_duration(script_duration)

        riddle_answer = TextClip(text=f"Answer: {riddle_answer}", font=font_file_path, font_size=50, color="white",bg_color="#e5383b",size=(940, 480), method='caption')
        riddle_answer = riddle_answer.with_position(("center",1340))
        riddle_answer = riddle_answer.with_start(script_duration-2)
        riddle_answer = riddle_answer.with_end(script_duration)


        final_video = CompositeVideoClip([final_video,bg,shadow,text, riddle_answer])

        final_video.write_videofile("output.mp4")
        logger.info("Audio and Video merged successfully")
        logger.info("Uploading video to YouTube...")
        final_video_path = f"{folder_path}\\output.mp4"
        

        youtube_description = """
        🔥 Welcome to The Riddle Feed!
        Can you solve today’s mind-twisting riddle? 🤯
        Watch closely, think fast, and drop your answer in the comments! 🧠💬
        I upload brand-new riddles every day — from easy brain teasers to impossible puzzles that will test your IQ! 😄✨

        👇 What to do next?
        ✔️ Comment your answer
        ✔️ Challenge your friends
        ✔️ Subscribe for daily riddles
        ✔️ Turn on the bell so you never miss a new one! 🔔

        Tags:
        """
        for tags in youtube_tags:
            youtube_description += f"\n#{tags.replace(" ","")}\n"

        yt_upload.upload_video(
            video_path=final_video_path,
            title=youtube_title,
            description=youtube_description,
            tags=youtube_tags,
            privacy="public"
        )
        logger.info("Video uploaded successfully")
        logger.info("Changing directory to Project Directory...")
        os.chdir(project_dir)
        logger.info(f"Successfully changed directory to {Path.cwd()}")
        logger.info("Deleting generated video and audio after 10 seconds...")
        sleep(10)
        shutil.rmtree(folder_path)
        logger.info("Successfully deleted video and audio")
    except Exception as e: 
        print("Something went wrong! Please logs to know more!")
        logger.error(f"an error occured: {e}")
        

while True:
    run_pending()
    sleep(1)
