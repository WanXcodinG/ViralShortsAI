import './tailwind.css';
import { Composition, staticFile } from "remotion";
import {
  CaptionedVideo,
  captionedVideoSchema,
} from "./CaptionedVideo";

// Each <Composition> is an entry in the sidebar!

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="CaptionedVideo"
      component={CaptionedVideo}
      schema={captionedVideoSchema}
      width={Math.floor(1080 / 2) * 2}
      height={Math.floor(1920 / 2) * 2}
      fps={30}
      durationInFrames={1800}
      defaultProps={{
        src: staticFile("final_video.mp4"),
      }}
    />
  );
};
