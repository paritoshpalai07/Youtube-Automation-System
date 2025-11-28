from dotenv import load_dotenv
from google import genai
from murf import Murf
from moviepy import VideoFileClip, TextClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip,ColorClip
import os
import json
import datetime
import requests

import yt_upload

load_dotenv()

client = genai.Client(api_key=os.getenv("Gemini_Api"))
exisiting_riddles = ""

with open(r"C:\Users\HP\Desktop\Youtube Automation\riddles.txt", "r") as f:
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

print("Request to gemini has been made....")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=riddle_prompt,
)

riddle = json.loads(response.text.replace("```","").replace("json",""))
print("Response from gemini has came...")

riddle_answer = riddle["answer"]
riddle_text = riddle["riddle"]
riddle_text = riddle_text.replace(". ",".\n")

riddle_str = ""
for key in riddle:
    riddle_str += riddle[key] + " "

prompt = f"based on the following write me a only one title for the youtube shorts video nothing else: '{riddle_str}'"

print("Now generating title of the video.....")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

youtube_title = response.text

print("Title generation finished!\nNow generating tags...")

prompt = f"based on the following give me a python list of youtube shorts video tags for the youtube shorts video, DO NOT add anything outside than python list: '{riddle_str}'"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
)

youtube_tags = response.text.replace("'''","").replace("python","").strip("[]").replace("'","").replace('"',"").split(",")
youtube_tags = [tags.strip() for tags in youtube_tags]
print(youtube_tags)
print(type(youtube_tags))
print("Youtube Tags generation finished!")

print("Adding riddle to riddle list...")
with open(r"C:\Users\HP\Desktop\Youtube Automation\riddles.txt", "a") as f:
    f.write(riddle["answer"])
    f.write("\n")
print("Successfully added riddle to existing riddle list!")

client = Murf(
    api_key=os.getenv("Murf_Api")
)

folder_name = f"{datetime.date.today()} {riddle["answer"]}"
folder_path = f"C:\\Users\\HP\\Desktop\\Youtube Automation\\Generated Videos\\{folder_name}"
os.mkdir(folder_path)
os.chdir(folder_path)
print("Folder created successfully! \nNow generating audio file...")

res = client.text_to_speech.generate(
        text=riddle_str,
        # voice_id="en-US-terrell",
        voice_id="en-US-ken",
    )

response = requests.get(res.audio_file)

with open(f"{folder_path}\\script.mp3", "wb") as f:
    f.write(response.content)

print(f"finished generating script.mp3")
print("Now merging Video and audio together...")

script_path = f"{folder_path}\\script.mp3"
bg_music_path = "C:\\Users\\HP\\Desktop\\Youtube Automation\\Musics\\bgmusic1.mp3"
video_clip_path = "C:\\Users\\HP\\Desktop\\Youtube Automation\\Resources\\character_edited.mp4"
font_file_path = "C:\\Users\\HP\\Desktop\\Youtube Automation\\fonts\\Permanent_Marker\\PermanentMarker-Regular.ttf"

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
final_video_path = f"{folder_path}\\output.mp4"
print(final_video_path)

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