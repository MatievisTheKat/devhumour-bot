import env from "dotenv";
import Snoowrap from "snoowrap";
import fs from "fs-extra";
import path from "path";
import same from "looks-same";
import jimp from "jimp";
import cron from "cron";
import { File } from "./types";

env.config();

const folder = path.resolve("cache");
const json = path.resolve("cache/_index.json");
const client = new Snoowrap({
  userAgent: "devhumour-bot",
  clientId: process.env.CLIENT_ID,
  clientSecret: process.env.CLIENT_SECRET,
  refreshToken: process.env.REFRESH_TOKEN,
});

new cron.CronJob("*/30 * * * *", run, null, true, "Europe/London");
run();

async function run() {
  await fs.mkdir(folder).catch((e) => {
    if (e.code !== "EEXIST") {
      console.error(e);
      process.exit(1);
    }
  });

  await fs.access("./reposts.txt").catch(async (e) => {
    if (e.code === "ENOENT") {
      await fs.writeFile("./reposts.txt", "");
    }
  });

  client.getNew("ProgrammerHumor", { limit: 500 }).then(async (n) => {
    const imgPosts = n.filter((n) => /.*\.(jpg|png|jpeg|webp)$$/g.test(n.url));
    const posts: Record<string, { similar: string[]; reposts: string[] }> = {};
    const prevContent = (await fs.readFile("./reposts.txt")).toString();
    const newPosts: string[] = [];

    console.log("[?] Downloading new images...");
    for (let i = 0; i < imgPosts.length; i++) {
      const post = imgPosts[i];
      const file = path.join(folder, `${post.id}.png`);
      const alreadyExists = await exists(file);

      if (!alreadyExists) {
        await download(post.url, file)
          .then(() => newPosts.push(post.id))
          .catch((e) => console.error(`[x] ${post.id} ${e.message}`));
      }
    }

    console.log("[?] Reading files from cache directory...");
    const _files = await fs.readdir(folder);
    const files = _files
      .filter((f) => f.endsWith(".png"))
      .map((f) => ({ path: path.resolve("cache", f), id: f.split(".")[0] }));
    const newFiles = files.filter((f) => newPosts.includes(f.id));

    console.log(`[?] Processing ${newFiles.length} images...`);
    for (let i = 0; i < newFiles.length; i++) {
      const file = newFiles[i];
      console.log(`  [-] Comparing ${file.id}... (${i + 1}/${newFiles.length})`);
      posts[file.id] = { similar: [], reposts: [] };

      for (const otherFile of files.filter((f) => f !== file)) {
        const equal = await isSimilar(file.path, otherFile.path);
        if (equal) posts[file.id].similar.push(otherFile.id);
      }

      const data = posts[file.id];

      if (data.similar) {
        const created = fixTimestamp(await client.getSubmission(file.id).created_utc);
        const timestamps = { [file.id]: created };

        for (const sim of data.similar) {
          timestamps[sim] = fixTimestamp(await client.getSubmission(sim).created_utc);
        }

        const sorted = Object.entries(timestamps).sort((a, b) => a[1] - b[1]);
        const og = sorted[0];
        const reposts = sorted.slice(1, sorted.length).map((r) => r[0]);
        posts[og[0]].reposts.push(...reposts);
      }
    }

    for (const [id, data] of Object.entries(posts)) {
      posts[id].similar = [...new Set(data.similar)];
      posts[id].reposts = [...new Set(data.reposts)];
    }

    const prevPosts = await getJson();
    await writeJson(Object.assign(prevPosts, posts));

    const postsWithReposts = Object.entries(posts)
      .filter((p) => p[1].reposts.length > 0)
      .map((p) => `${p[0]}: ${p[1].reposts.join(", ")}`)
      .join("\n");

    await fs.writeFile("./reposts.txt", `${postsWithReposts}`);
    console.log("\n");
  });
}

function getJson() {
  return new Promise<File>((resolve, reject) => {
    fs.readJSON(json)
      .then(resolve)
      .catch(() => resolve({}));
  });
}

async function writeJson(data: File) {
  await fs.writeJSON(json, data, { spaces: 2 });
}

function fixTimestamp(t: number) {
  const d = new Date(0);
  d.setUTCSeconds(t);
  return d.getTime();
}

function isSimilar(base: string, img: string) {
  return new Promise<boolean>((resolve, reject) => {
    same(base, img, (err, res) => {
      if (err) return reject(err);
      else resolve(res.equal || false);
    });
  });
}

function download(url: string, file: string) {
  return new Promise<void>((resolve, reject) => {
    jimp
      .read(url)
      .then((i) => {
        i.write(file);
        resolve();
      })
      .catch(reject);
  });
}

function exists(p: string) {
  return new Promise<boolean>((resolve, reject) => {
    fs.access(p, (err) => {
      if (!err) resolve(true);
      else if (err.code === "ENOENT") resolve(false);
      else reject(err);
    });
  });
}
