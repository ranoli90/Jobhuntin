import React from "react";
import { Link } from "react-router-dom";
import guides from "../../data/guides.json";

interface RelatedGuidesProperties {
  currentGuideSlug: string;
}

const RelatedGuides: React.FC<RelatedGuidesProperties> = ({
  currentGuideSlug,
}) => {
  const relatedGuides = Object.entries(guides as Record<string, any>)
    .filter(([slug]) => slug !== currentGuideSlug)
    .slice(0, 3);

  if (relatedGuides.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-100 p-6 rounded-lg my-8">
      <h3 className="text-xl font-bold mb-4">Related Guides</h3>
      <div className="grid gap-8">
        {relatedGuides.map(([slug, guide]) => (
          <Link
            to={`/guides/${slug}`}
            key={slug}
            className="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow"
          >
            <h3 className="text-xl font-bold mb-2">{guide.title}</h3>
            <p className="text-slate-600">{guide.readTime}</p>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default RelatedGuides;
