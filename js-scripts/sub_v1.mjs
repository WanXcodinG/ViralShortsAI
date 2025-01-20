import { execSync } from "node:child_process";
import {
  existsSync,
  rmSync,
  writeFileSync,
  lstatSync,
  mkdirSync,
  readdirSync,
} from "node:fs";
import path from "path";
import chokidar from "chokidar";
import {
  WHISPER_LANG,
  WHISPER_MODEL,
  WHISPER_PATH,
  WHISPER_VERSION,
} from "./whisper-config.mjs";
import {
  downloadWhisperModel,
  installWhisperCpp,
  transcribe,
  toCaptions,
} from "@remotion/install-whisper-cpp";

const processedFiles = new Set(); // Keep track of processed files

const extractToTempAudioFile = (fileToTranscribe, tempOutFile) => {
  execSync(
    `npx remotion ffmpeg -i ${fileToTranscribe} -ar 16000 ${tempOutFile} -y`,
    { stdio: ["ignore", "inherit"] }
  );
};

const subFile = async (filePath, fileName, folder) => {
  const outPath = path.join(
    process.cwd(),
    "public",
    folder,
    fileName.replace(".wav", ".json")
  );

  const whisperCppOutput = await transcribe({
    inputPath: filePath,
    model: WHISPER_MODEL,
    tokenLevelTimestamps: true,
    whisperPath: WHISPER_PATH,
    printOutput: false,
    translateToEnglish: false,
    language: WHISPER_LANG,
    splitOnWord: true,
  });

  const { captions } = toCaptions({
    whisperCppOutput,
  });
  writeFileSync(
    outPath.replace("webcam", "subs"),
    JSON.stringify(captions, null, 2)
  );
};

const processVideo = async (fullPath, entry, directory) => {
  if (processedFiles.has(fullPath)) {
    return; // Skip already processed files
  }

  if (
    !fullPath.endsWith(".mp4") &&
    !fullPath.endsWith(".webm") &&
    !fullPath.endsWith(".mkv") &&
    !fullPath.endsWith(".mov")
  ) {
    return;
  }

  const isTranscribed = existsSync(
    fullPath
      .replace(/.mp4$/, ".json")
      .replace(/.mkv$/, ".json")
      .replace(/.mov$/, ".json")
      .replace(/.webm$/, ".json")
      .replace("webcam", "subs")
  );

  if (isTranscribed) {
    processedFiles.add(fullPath); // Mark as processed
    return;
  }

  console.log("Processing file:", fullPath);

  let shouldRemoveTempDirectory = false;
  if (!existsSync(path.join(process.cwd(), "temp"))) {
    mkdirSync(`temp`);
    shouldRemoveTempDirectory = true;
  }

  const tempWavFileName = entry.split(".")[0] + ".wav";
  const tempOutFilePath = path.join(process.cwd(), `temp/${tempWavFileName}`);

  extractToTempAudioFile(fullPath, tempOutFilePath);
  await subFile(tempOutFilePath, tempWavFileName, path.relative("public", directory));

  if (shouldRemoveTempDirectory) {
    rmSync(path.join(process.cwd(), "temp"), { recursive: true });
  }

  processedFiles.add(fullPath); // Mark as processed
};

const processDirectory = async (directory) => {
  const entries = readdirSync(directory).filter((f) => f !== ".DS_Store");

  for (const entry of entries) {
    const fullPath = path.join(directory, entry);
    const stat = lstatSync(fullPath);

    if (stat.isDirectory()) {
      await processDirectory(fullPath); // Recurse into subdirectories
    } else {
      await processVideo(fullPath, entry, directory);
    }
  }
};

await installWhisperCpp({ to: WHISPER_PATH, version: WHISPER_VERSION });
await downloadWhisperModel({ folder: WHISPER_PATH, model: WHISPER_MODEL });

const watchDirectories = [
  process.cwd(),
  path.join(process.cwd(), "../media/videos"), // Include the media/videos directory
];

console.log(`Watching directories for changes: ${watchDirectories}`);

const watcher = chokidar.watch(watchDirectories, {
  ignored: /(^|[\/\\])\../, // Ignore dotfiles
  persistent: true,
});

watcher.on("add", async (filePath) => {
  try {
    if (
      filePath.endsWith(".mp4") ||
      filePath.endsWith(".webm") ||
      filePath.endsWith(".mkv") ||
      filePath.endsWith(".mov")
    ) {
      console.log(`Detected new file: ${filePath}`);
      const directory = path.dirname(filePath);
      const fileName = path.basename(filePath);
      await processVideo(filePath, fileName, directory);
    }
  } catch (error) {
    console.error(`Error processing file ${filePath}:`, error);
  }
});

watcher.on("error", (error) => {
  console.error(`Watcher error: ${error}`);
});

// Process all files in the directory initially
for (const dir of watchDirectories) {
  await processDirectory(dir);
}