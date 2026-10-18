import type { MetadataRoute } from "next";
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://usevoicy.app",
      lastModified: "2026-10-18",
      changeFrequency: "monthly",
      priority: 1,
    },
    {
      url: "https://usevoicy.app/adobe-podcast-alternative",
      lastModified: "2026-10-18",
      changeFrequency: "monthly",
      priority: 0.9,
    },
    {
      url: "https://usevoicy.app/privacy",
      lastModified: "2026-09-22",
      changeFrequency: "yearly",
      priority: 0.2,
    },
  ];
}
