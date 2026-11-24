#!/usr/bin/env node
// Generate one cohesive high-key beauty set: 7 stills then 7 five-second clips.
// Run from the build folder with KIE_AI_API_KEY exported.
//   node generate.mjs all | stills | shots | probe

import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";

const ROOT = path.resolve(".");
const OUT = path.join(ROOT, "out");
fs.mkdirSync(OUT, { recursive: true });

// Verbatim in every prompt. This is what makes seven separate jobs one shoot.
const STYLE = [
  "Editorial beauty photography on a seamless bone-white cyclorama.",
  "One large soft overhead source and a huge white bounce, near-shadowless with a single soft contact shadow.",
  "High key, gentle contrast. Colour grade of warm white, pale neutrals and one muted raspberry accent.",
  "Medium-format sharpness, fine film grain, honest skin texture.",
  "Photographic realism, no CGI, no clay, no illustration, no digital glow, no plastic sheen, no text, no watermark.",
].join(" ");

const SCENES = [
  {
    key: "01-hero",
    still: "A lash technician in a crisp white tunic carefully fitting lashes for a seated client in a bright studio. The two women are centre-right, a soft white towel in the near foreground overlapping the frame, a pale wall behind. Large empty bright space across the lower left for copy. Calm, skilled, real.",
    move: "The camera drifts slowly and steadily forward toward the technician's hands, a single gentle dolly-in with a very slight downward tilt. Both women stay still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "02-phone",
    still: "A beautician's hand beside a client's shoulder, a phone face up on a white counter with a completely blank unlit screen. The hand and phone sit centre-right. Large empty bright space across the upper left for copy. No text, no icons, no interface, no readable screen.",
    move: "The camera pushes slowly and steadily in toward the phone on the counter, one continuous dolly-in, the hand and phone perfectly still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "03-diary",
    still: "A clean open appointment diary on a white desk, fresh blank pages with simple printed columns and no writing, a stylist's hand just resting at the edge. The diary sits centre-right. Large empty bright space across the left of the frame for copy. No readable words, no numbers, no brand marks.",
    move: "The camera glides slowly and steadily downward and forward over the open diary, one continuous move, the hand and diary perfectly still. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "04-nails",
    still: "Extreme close beauty detail of a client's hands with freshly finished neutral pink nails resting on a folded white towel, one hand holding a glass nail file. Hands centre-right. Large empty bright space across the upper left for copy. Clean, tactile, no jewellery logos.",
    move: "The camera creeps slowly and steadily closer to the finished nails, one continuous macro dolly-in, the hands perfectly still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "05-african-hair",
    still: "A Black hair specialist's hands working patiently on a client's braids, the client's textured hair and neat braids clearly visible from behind and to the side, both people in a bright white studio. Subjects centre-right. Large empty bright space across the left of the frame for copy. Respectful, authentic, skilled, no styling clichés.",
    move: "The camera moves slowly and steadily sideways along the line of braids, one continuous gentle lateral drift, the hands and client perfectly still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "06-brows",
    still: "A brow artist shaping a client's eyebrows in a bright treatment room, the client's face in profile on the right, the artist's hand and a fine brush in the middle ground, white surfaces behind. Large empty bright space across the left of the frame for copy. Calm, precise, real skin texture.",
    move: "The camera pushes slowly and steadily toward the artist's hand and the client's brow, one continuous dolly-in, both people perfectly still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
  {
    key: "07-replies",
    still: "A beautician's hands holding a phone upright with a completely blank pale screen, sitting at a white salon desk between appointments. Hands and phone centre-right. Large empty bright space across the left of the frame for copy. No text, no icons, no interface, no readable screen.",
    move: "The camera rises slowly and steadily up the phone toward the hands, one continuous tilt, the hands perfectly still and in frame throughout. One continuous take, no cuts, no camera shake, no zoom snap.",
  },
];

function run(cmd, args, label) {
  return new Promise((resolve, reject) => {
    const p = spawn(cmd, args, { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] });
    let err = "";
    p.stdout.on("data", (d) => process.stdout.write(d));
    p.stderr.on("data", (d) => { err += d.toString(); process.stderr.write(d); });
    p.on("close", (code) => code === 0 ? resolve() : reject(new Error(`${label} exited ${code}: ${err.slice(-500)}`)));
  });
}

async function pool(items, limit, worker) {
  let i = 0;
  const runners = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const item = items[i++];
      await worker(item);
    }
  });
  await Promise.all(runners);
}

const mode = process.argv[2] || "all";
const key = process.env.KIE_AI_API_KEY;
if (!key && mode !== "probe") {
  console.error("KIE_AI_API_KEY must be exported in the environment");
  process.exit(1);
}
const env = { ...process.env, KIE_AI_API_KEY: key };

async function probe() {
  await run("node", ["kie.mjs", "probe"], "probe");
}

if (mode === "probe") await probe();

if (mode === "all" || mode === "stills") {
  await pool(SCENES, 3, async (s) => {
    const file = path.join(OUT, `${s.key}.png`);
    if (fs.existsSync(file)) { console.log(`exists ${file}`); return; }
    await run("node", ["kie.mjs", "still", `${STYLE}\n\n${s.still}`, file, "--ar", "16:9"], `still ${s.key}`);
  });
  if (mode === "all") await probe();
}

if (mode === "all" || mode === "shots") {
  await pool(SCENES, 2, async (s) => {
    const head = path.join(OUT, `${s.key}.png`);
    const file = path.join(OUT, `${s.key}.mp4`);
    if (fs.existsSync(file)) { console.log(`exists ${file}`); return; }
    await run("node", ["kie.mjs", "shot", s.move, head, file, "--dur", "5"], `shot ${s.key}`);
  });
  if (mode === "all") await probe();
}

console.log("done:", mode);
