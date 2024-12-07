import fs from 'fs/promises';

// Threshold for silence in milliseconds
const SILENCE_THRESHOLD = 2000; // 2000ms

// Confidence threshold
const CONFIDENCE_THRESHOLD = 0.2;

// Input and output file paths
const transcriptFilePath = './public/pawesome-closing.json';
const silenceFilePath = './public/silence.json';

// Function to detect silence periods
const detectSilence = async () => {
  try {
    // Read the transcript JSON file
    const data = await fs.readFile(transcriptFilePath, 'utf8');
    const transcript = JSON.parse(data);

    // Filter out words below the confidence threshold
    const filteredTranscript = transcript.filter(word => word.confidence >= CONFIDENCE_THRESHOLD);

    // Sort the transcript by timestamp
    filteredTranscript.sort((a, b) => a.timestampMs - b.timestampMs);

    const silencePeriods = [];

    // Initialize previous end time
    let prevEndMs = 0;

    // Add silence before the first word if it starts after 0ms
    if (filteredTranscript.length > 0 && filteredTranscript[0].timestampMs > 0) {
      silencePeriods.push({ fromMs: 0, toMs: filteredTranscript[0].timestampMs });
      prevEndMs = filteredTranscript[0].timestampMs;
    }

    // Detect silent periods between words using timestampMs
    for (let i = 1; i < filteredTranscript.length; i++) {
      const current = filteredTranscript[i];
      const gap = current.timestampMs - prevEndMs;

      if (gap > SILENCE_THRESHOLD) {
        silencePeriods.push({ fromMs: prevEndMs, toMs: current.timestampMs });
      }

      // Update previous end time
      prevEndMs = current.timestampMs;
    }

    // Optionally, add silence after the last word till the end of the video
    // You'll need the video's total duration for this
    // Example:
    // const videoDurationMs = 60000; // 60 seconds
    // if (prevEndMs < videoDurationMs) {
    //   silencePeriods.push({ fromMs: prevEndMs, toMs: videoDurationMs });
    // }

    // Write the silence periods to a file
    await fs.writeFile(silenceFilePath, JSON.stringify(silencePeriods, null, 2));
    console.log(`Silence periods saved to ${silenceFilePath}`);
  } catch (err) {
    console.error('Error processing silence periods:', err);
  }
};

// Run the function
detectSilence();