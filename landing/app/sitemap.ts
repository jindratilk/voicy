import type { MetadataRoute } from "next";
export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: "https://usevoicy.app",
      lastModified: "2026-09-22",
      changeFrequency: "monthly",
      priority: 1,
    },
    {
      url: "https://usevoicy.app/privacy",
      lastModified: "2026-09-22",
      changeFrequency: "yearly",
      priority: 0.2,
    },
  ];
}
