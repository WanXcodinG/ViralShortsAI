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
  const metadata = await getVideoMetadata(props.src);

  return {
    fps,
    durationInFrames: Math.floor(metadata.durationInSeconds * fps),
  };
};

const SWITCH_CAPTIONS_EVERY_MS = 1200;

export const CaptionedVideo: React.FC<{ src: string }> = ({ src }) => {
  const [subtitles, setSubtitles] = useState<Caption[]>([]);
  const [zoomEffects, setZoomEffects] = useState<
    { timestampMs: number; zoomEffect: boolean; zoomLevel: number }[]
  >([]);
  const [handle] = useState(() => delayRender());
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const subtitlesFile = src.replace(/\.\w+$/, ".json");

  const fetchSubtitles = useCallback(async () => {
    try {
      const res = await fetch(subtitlesFile);
      const data = await res.json();
      loadFont();
      setSubtitles(data);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [handle, subtitlesFile]);

  const fetchZoomEffects = useCallback(async () => {
    try {
      const res = await fetch(staticFile("zoom_effects.json"));
      const data = await res.json();
      setZoomEffects(data.effects);
    } catch (e) {
      console.error("Failed to load zoom effects:", e);
    }
  }, []);

  useEffect(() => {
    fetchSubtitles();
    fetchZoomEffects();
  }, [fetchSubtitles, fetchZoomEffects]);

  const { pages } = useMemo(() => {
    return createTikTokStyleCaptions({
      combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
      captions: subtitles ?? [],
    });
  }, [subtitles]);

  // Convert current frame to timestamp in milliseconds
  const currentTimestampMs = useMemo(() => {
    return (frame / fps) * 1000;
  }, [frame, fps]);

  // Determine the current zoom level based on the current timestamp
  const currentZoom = useMemo(() => {
    if (!zoomEffects || zoomEffects.length === 0) {
      console.warn("No zoom effects found.");
      return 1; // Default zoom level for no effects
    }

    // Find the latest zoom effect where timestampMs <= currentTimestampMs
    const activeZoom = zoomEffects
      .filter((effect) => effect.zoomEffect && effect.timestampMs <= currentTimestampMs)
      .sort((a, b) => b.timestampMs - a.timestampMs)[0];

    if (activeZoom) {
      console.log("Active Zoom Effect Found:", activeZoom);
      return activeZoom.zoomLevel;
    }

    // If no active zoom effect is found, return default zoom level
    return 1;
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
            key={index}
            from={subtitleStartFrame}
            durationInFrames={durationInFrames}
          >
            <SubtitlePage key={index} page={page} />
          </Sequence>
        );
      })}

      {/* No Captions Fallback */}
      {!subtitles.length && <NoCaptionFile />}
    </AbsoluteFill>
  );
};