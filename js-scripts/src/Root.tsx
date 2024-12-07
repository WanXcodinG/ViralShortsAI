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
      width={1080}
      height={1920}
      fps={30}
      durationInFrames={1800}
      defaultProps={{
        src: staticFile("pawesome-closing-trimmed.mp4"),
      }}
    />
  );
};
