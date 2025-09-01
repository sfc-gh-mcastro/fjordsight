from youtube_transcript_api import YouTubeTranscriptApi
import sys
import yt_dlp
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

def extract_video_id(url_or_id):
    """Extract video ID from YouTube URL or return the ID if already provided."""
    if 'youtube.com' in url_or_id or 'youtu.be' in url_or_id:
        if 'v=' in url_or_id:
            return url_or_id.split('v=')[1].split('&')[0]
        elif 'youtu.be' in url_or_id:
            return url_or_id.split('/')[-1].split('?')[0]
    return url_or_id

def get_video_metadata(video_id):
    """Extract metadata from YouTube video using yt-dlp."""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=False)
            
            metadata = {
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader', 'Unknown Channel'),
                'upload_date': info.get('upload_date', 'Unknown Date'),
                'duration': info.get('duration', 0),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'description': info.get('description', 'No description available'),
                'tags': info.get('tags', []),
                'url': f'https://www.youtube.com/watch?v={video_id}'
            }
            
            # Format upload date
            if metadata['upload_date'] and metadata['upload_date'] != 'Unknown Date':
                try:
                    date_obj = datetime.strptime(metadata['upload_date'], '%Y%m%d')
                    metadata['formatted_date'] = date_obj.strftime('%B %d, %Y')
                except:
                    metadata['formatted_date'] = metadata['upload_date']
            else:
                metadata['formatted_date'] = 'Unknown Date'
            
            # Format duration
            if metadata['duration']:
                hours = metadata['duration'] // 3600
                minutes = (metadata['duration'] % 3600) // 60
                seconds = metadata['duration'] % 60
                if hours > 0:
                    metadata['formatted_duration'] = f"{hours}:{minutes:02d}:{seconds:02d}"
                else:
                    metadata['formatted_duration'] = f"{minutes}:{seconds:02d}"
            else:
                metadata['formatted_duration'] = 'Unknown'
            
            return metadata
            
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return {
            'title': 'Unknown Title',
            'uploader': 'Unknown Channel',
            'formatted_date': 'Unknown Date',
            'formatted_duration': 'Unknown',
            'view_count': 0,
            'like_count': 0,
            'description': 'No description available',
            'tags': [],
            'url': f'https://www.youtube.com/watch?v={video_id}'
        }

def get_transcript(video_id, languages=['en']):
    """Fetch transcript for a YouTube video."""
    try:
        # Create an instance of YouTubeTranscriptApi and fetch the transcript
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id, languages=languages)
        
        print(f"Successfully fetched transcript for video: {video_id}")
        print(f"Total segments: {len(transcript)}")
        print("-" * 50)
        
        # The fetch method returns a FetchedTranscript object with FetchedTranscriptSnippet items
        full_text = ""
        for entry in transcript:
            timestamp = f"[{entry.start:.2f}s]"
            text = entry.text.strip()
            print(f"{timestamp} {text}")
            full_text += f"{text} "
        
        print("-" * 50)
        print(f"Full transcript length: {len(full_text)} characters")
        
        return transcript, full_text
        
    except Exception as e:
        print(f"An error occurred while fetching transcript: {e}")
        return None, None

def group_transcript_by_time(transcript, interval_minutes=1):
    """Group transcript segments into time intervals (default 1 minute)."""
    if not transcript:
        return []
    
    grouped_segments = []
    interval_seconds = interval_minutes * 60
    current_group = {
        'start_time': 0,
        'end_time': 0,
        'text_segments': []
    }
    
    for entry in transcript:
        # If this entry starts beyond the current interval, start a new group
        if entry.start >= current_group['start_time'] + interval_seconds:
            # Save the previous group if it has content
            if current_group['text_segments']:
                current_group['combined_text'] = ' '.join(current_group['text_segments']).strip()
                grouped_segments.append(current_group.copy())
            
            # Start new group
            current_group = {
                'start_time': (entry.start // interval_seconds) * interval_seconds,
                'end_time': ((entry.start // interval_seconds) + 1) * interval_seconds,
                'text_segments': []
            }
        
        # Add text to current group (skip music and empty segments)
        text = entry.text.strip()
        if text and text not in ['[Music]', '[Applause]', '[Laughter]']:
            current_group['text_segments'].append(text)
    
    # Don't forget the last group
    if current_group['text_segments']:
        current_group['combined_text'] = ' '.join(current_group['text_segments']).strip()
        grouped_segments.append(current_group)
    
    return grouped_segments

def create_pdf_report(video_id, metadata, transcript, output_path=None, interval_minutes=1):
    """Create a PDF report with video metadata and transcript."""
    if not output_path:
        # Create output directory if it doesn't exist
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate filename based on video title and date
        safe_title = "".join(c for c in metadata['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{output_dir}/{safe_title}_{timestamp}.pdf"
    
    try:
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        transcript_style = ParagraphStyle(
            'TranscriptStyle',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=4,
            leftIndent=20
        )
        
        # Build PDF content
        story = []
        
        # Title page
        story.append(Paragraph("YouTube Video Transcript Report", title_style))
        story.append(Spacer(1, 20))
        
        # Video metadata section
        story.append(Paragraph("Video Information", heading_style))
        story.append(Paragraph(f"<b>Title:</b> {metadata['title']}", normal_style))
        story.append(Paragraph(f"<b>Channel:</b> {metadata['uploader']}", normal_style))
        story.append(Paragraph(f"<b>Upload Date:</b> {metadata['formatted_date']}", normal_style))
        story.append(Paragraph(f"<b>Duration:</b> {metadata['formatted_duration']}", normal_style))
        story.append(Paragraph(f"<b>Views:</b> {metadata['view_count']:,}" if metadata['view_count'] else "<b>Views:</b> N/A", normal_style))
        story.append(Paragraph(f"<b>Likes:</b> {metadata['like_count']:,}" if metadata['like_count'] else "<b>Likes:</b> N/A", normal_style))
        story.append(Paragraph(f"<b>URL:</b> {metadata['url']}", normal_style))
        story.append(Spacer(1, 20))
        
        # Description section
        if metadata['description'] and metadata['description'] != 'No description available':
            story.append(Paragraph("Description", heading_style))
            # Limit description length and handle HTML entities
            description = metadata['description'][:500] + "..." if len(metadata['description']) > 500 else metadata['description']
            description = description.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(description, normal_style))
            story.append(Spacer(1, 20))
        
        # Tags section
        if metadata['tags']:
            story.append(Paragraph("Tags", heading_style))
            tags_text = ", ".join(metadata['tags'][:20])  # Limit to first 20 tags
            story.append(Paragraph(tags_text, normal_style))
            story.append(Spacer(1, 20))
        
        # Page break before transcript
        story.append(PageBreak())
        
        # Transcript section
        story.append(Paragraph(f"Video Transcript (grouped by {interval_minutes} minute intervals)", heading_style))
        story.append(Spacer(1, 12))
        
        if transcript:
            # Group transcript segments by time intervals
            grouped_segments = group_transcript_by_time(transcript, interval_minutes)
            
            for i, segment in enumerate(grouped_segments):
                # Format time range
                start_minutes = int(segment['start_time'] // 60)
                start_seconds = int(segment['start_time'] % 60)
                end_minutes = int(segment['end_time'] // 60)
                end_seconds = int(segment['end_time'] % 60)
                
                time_range = f"[{start_minutes:02d}:{start_seconds:02d} - {end_minutes:02d}:{end_seconds:02d}]"
                
                # Escape HTML entities in transcript text
                text = segment['combined_text'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Add the grouped segment
                story.append(Paragraph(f"<b>{time_range}</b>", transcript_style))
                story.append(Paragraph(text, transcript_style))
                story.append(Spacer(1, 8))
        else:
            story.append(Paragraph("Transcript not available", normal_style))
        
        # Generate PDF
        doc.build(story)
        
        print(f"PDF report generated successfully: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None

if __name__ == "__main__":
    # Check for help argument
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("YouTube Video Transcript to PDF Generator")
        print("=" * 50)
        print("Usage:")
        print("  python video_transcripts_ingestion.py [VIDEO_ID_OR_URL] [INTERVAL_MINUTES]")
        print()
        print("Arguments:")
        print("  VIDEO_ID_OR_URL    YouTube video ID or full URL (default: NnAc9qe68GI)")
        print("  INTERVAL_MINUTES   Time interval for grouping transcript (default: 1)")
        print()
        print("Examples:")
        print("  python video_transcripts_ingestion.py")
        print("  python video_transcripts_ingestion.py NnAc9qe68GI 2")
        print("  python video_transcripts_ingestion.py 'https://www.youtube.com/watch?v=VIDEO_ID' 1.5")
        print()
        print("Output:")
        print("  - PDF file saved to 'output/' directory")
        print("  - Contains video metadata and grouped transcript")
        sys.exit(0)
    
    # Default video ID - Aquaculture conference
    video_id = 'NnAc9qe68GI'
    interval_minutes = 1  # Default to 1-minute intervals
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        video_id = extract_video_id(sys.argv[1])
    
    if len(sys.argv) > 2:
        try:
            interval_minutes = float(sys.argv[2])
            if interval_minutes <= 0:
                print("Warning: Interval must be positive, using default 1 minute")
                interval_minutes = 1
        except ValueError:
            print("Warning: Invalid interval format, using default 1 minute")
            interval_minutes = 1
    
    print(f"Processing video ID: {video_id}")
    print(f"Transcript grouping: {interval_minutes} minute intervals")
    print("=" * 60)
    
    # Fetch video metadata
    print("Fetching video metadata...")
    metadata = get_video_metadata(video_id)
    
    print(f"Title: {metadata['title']}")
    print(f"Channel: {metadata['uploader']}")
    print(f"Upload Date: {metadata['formatted_date']}")
    print(f"Duration: {metadata['formatted_duration']}")
    print("=" * 60)
    
    # Fetch transcript
    print("Fetching transcript...")
    transcript, full_text = get_transcript(video_id)
    
    if transcript:
        print("=" * 60)
        print(f"Creating PDF report with {interval_minutes}-minute transcript intervals...")
        pdf_path = create_pdf_report(video_id, metadata, transcript, interval_minutes=interval_minutes)
        
        if pdf_path:
            print(f"✅ PDF report created successfully!")
            print(f"📄 File location: {pdf_path}")
            
            # Show preview of grouping
            grouped_segments = group_transcript_by_time(transcript, interval_minutes)
            print(f"📊 Transcript grouped into {len(grouped_segments)} segments ({interval_minutes}-minute intervals)")
        else:
            print("❌ Failed to create PDF report")
    else:
        print("❌ Could not fetch transcript, skipping PDF generation")