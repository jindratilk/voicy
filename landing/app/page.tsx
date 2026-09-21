import Landing from "@/components/Landing";
import { faqs, site } from "@/lib/site";
export default function Page() {
  const data = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SoftwareApplication",
        name: "Voicy",
        url: site.url,
        applicationCategory: "MultimediaApplication",
        operatingSystem: "macOS 14 or later, Apple Silicon",
        softwareVersion: site.version,
        description:
          "Free open-source AI speech enhancement for Mac, processed locally with AuK.",
        offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
        downloadUrl: site.url + "/api/download",
        license: site.github + "/blob/main/LICENSE",
      },
      {
        "@type": "FAQPage",
        mainEntity: faqs.map(([q, a]) => ({
          "@type": "Question",
          name: q,
          acceptedAnswer: { "@type": "Answer", text: a },
        })),
      },
    ],
  };
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(data).replace(/</g, "\\u003c"),
        }}
      />
      <Landing />
    </>
  );
}
