import {FaXTwitter} from "react-icons/fa6";

const footerLines = [GithubLine, XLine];

export default function FooterLine() {
  const index = Math.round(Math.random() * (footerLines.length - 1));
  const Line = footerLines[index];

  return <Line />;
}

function GithubLine() {
  return (
    <a
      href="https://github.com/limanAI/dyvy"
      target="_blank"
      rel="noopener noreferrer"
      className="link link-hover inline-flex items-center gap-1"
    >
      Star us on GitHub
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="feather feather-star"
      >
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    </a>
  );
}

function XLine() {
  return (
    <a href="https://x.com" target="_blank" rel="noopener noreferrer" className="link link-hover inline-flex gap-1">
      <span>Share on</span>
      <FaXTwitter className="w-4 h-4 relative -top-0.5" />
    </a>
  );
}
