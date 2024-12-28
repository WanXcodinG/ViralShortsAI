import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AbsoluteFill,
  cancelRender,
  continueRender,
  delayRender,
  Sequence,
  useVideoConfig,
  useCurrentFrame,
  OffthreadVideo,
  staticFile,
} from "remotion";
import { loadFont } from "../load-font";
import { z } from "zod";
import SubtitlePage from "./SubtitlePage";
import { getVideoMetadata } from "@remotion/media-utils";
import { NoCaptionFile } from "./NoCaptionFile";
import { Caption, createTikTokStyleCaptions } from "@remotion/captions";

export interface CaptionedVideoProps {
  src: string;
}

export const captionedVideoSchema = z.object({
  src: z.string(),
});

export const calculateCaptionedVideoMetadata = async ({ props }: { props: CaptionedVideoProps }) => {
  const fps = 30;
  try {
    const metadata = await getVideoMetadata(props.src);
    if (!metadata || !metadata.durationInSeconds) {
      throw new Error("Invalid video metadata");
    }
    return {
      fps,
      durationInFrames: Math.floor(metadata.durationInSeconds * fps),
    };
  } catch (e) {
    console.error("Error fetching video metadata:", e);
    return { fps, durationInFrames: 0 }; // Default to zero frames to prevent crashes
  }
};

const SWITCH_CAPTIONS_EVERY_MS = 1200;

export const CaptionedVideo: React.FC<{ src: string }> = ({ src }) => {
  const [subtitles, setSubtitles] = useState<Caption[]>([]);
  const [zoomEffects, setZoomEffects] = useState<
    { timestampMs: number; zoomEffect: boolean; zoomLevel: number }[]
  >([]);
  const [handle] = useState(() => delayRender());
  const { width, height, fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const subtitlesFile = src.replace(/\.\w+$/, ".json");

  // Validate video dimensions
  useEffect(() => {
    if (!width || !height) {
      console.error("Invalid video dimensions:", { width, height });
      throw new Error("Invalid video dimensions.");
    }
    if (width % 2 !== 0 || height % 2 !== 0) {
      console.warn("Dimensions are not divisible by 2:", { width, height });
    }
  }, [width, height]);

  const fetchSubtitles = useCallback(async () => {
    try {
      const res = await fetch(subtitlesFile);
      if (!res.ok) {
        throw new Error(`Failed to fetch subtitles: ${res.statusText}`);
      }
      const data = await res.json();
      loadFont();
      setSubtitles(data);
      continueRender(handle);
    } catch (e) {
      console.error("Subtitles fetch error:", e);
      cancelRender(e);
    }
  }, [handle, subtitlesFile]);

  const fetchZoomEffects = useCallback(async () => {
    try {
      const res = await fetch(staticFile("zoom_effects.json"));
      if (!res.ok) {
        throw new Error(`Failed to fetch zoom effects: ${res.statusText}`);
      }
      const data = await res.json();
      setZoomEffects(data.effects);
    } catch (e) {
      console.error("Zoom effects fetch error:", e);
    }
  }, []);

  useEffect(() => {
    fetchSubtitles();
    fetchZoomEffects();
  }, [fetchSubtitles, fetchZoomEffects]);

  const { pages } = useMemo(() => {
    if (!subtitles || subtitles.length === 0) {
      console.warn("No subtitles found.");
      return { pages: [] }; // Fallback if no subtitles are found
    }
    return createTikTokStyleCaptions({
      combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
      captions: subtitles,
    });
  }, [subtitles]);

  const currentTimestampMs = useMemo(() => {
    return (frame / fps) * 1000;
  }, [frame, fps]);

  const currentZoom = useMemo(() => {
    if (!zoomEffects || zoomEffects.length === 0) {
      console.warn("No zoom effects found.");
      return 1; // Default zoom level for no effects
    }

    const activeZoom = zoomEffects
      .filter((effect) => effect.zoomEffect && effect.timestampMs <= currentTimestampMs)
      .sort((a, b) => b.timestampMs - a.timestampMs)[0];

    return activeZoom ? activeZoom.zoomLevel : 1; // Default zoom level
  }, [currentTimestampMs, zoomEffects]);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      {/* Video Container with Zoom Effect */}
      <AbsoluteFill
        style={{
          transform: `scale(${currentZoom})`,
        }}
      >
        <OffthreadVideo
          style={{
            objectFit: "cover",
          }}
          src={src}
        />
      </AbsoluteFill>

      {/* Render Captions */}
      {pages.map((page, index) => {
        const nextPage = pages[index + 1] ?? null;
        const subtitleStartFrame = (page.startMs / 1000) * fps;
        const subtitleEndFrame = Math.min(
          nextPage ? (nextPage.startMs / 1000) * fps : Infinity,
          subtitleStartFrame + SWITCH_CAPTIONS_EVERY_MS
        );
        const durationInFrames = subtitleEndFrame - subtitleStartFrame;

        if (durationInFrames <= 0) {
          return null;
        }

        return (
          <Sequence
            key={`${subtitleStartFrame}-${index}`} // Ensure unique keys
            from={subtitleStartFrame}
            durationInFrames={durationInFrames}
          >
            <SubtitlePage page={page} />
          </Sequence>
        );
      })}

      {/* No Captions Fallback */}
      {!subtitles.length && <NoCaptionFile />}
    </AbsoluteFill>
  );
};