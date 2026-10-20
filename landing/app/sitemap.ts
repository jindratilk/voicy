import type { MetadataRoute } from "next";
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://usevoicy.app",
      lastModified: "2026-10-20T22:05:56.992491+00:00",
      changeFrequency: "monthly",
      priority: 1,
    },
    {
      url: "https://usevoicy.app/adobe-podcast-alternative",
      lastModified: "2026-10-20",
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: "https://usevoicy.app/privacy",
      lastModified: "2026-10-19",
      changeFrequency: "yearly",
      priority: 0.2,
    },
  ];
}
