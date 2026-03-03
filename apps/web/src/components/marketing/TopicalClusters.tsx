import React from 'react';

interface TopicalClustersProps {
  clusters: string[][];
}

const TopicalClusters: React.FC<TopicalClustersProps> = ({ clusters }) => {
  if (!clusters || clusters.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-100 p-6 rounded-lg my-8">
      <h3 className="text-xl font-bold mb-4">Explore Topic Clusters</h3>
      <div className="space-y-4">
        {clusters.map((cluster, index) => (
          <div key={index}>
            <h4 className="font-bold text-lg mb-2">Cluster #{index + 1}</h4>
            <div className="flex flex-wrap gap-4">
              {cluster.map((topic) => {
                const slug = topic.toLowerCase().replace(/ /g, '-');
                const url = `/topics/${slug}`;
                return (
                  <a href={url} key={slug} className="bg-white hover:bg-slate-200 text-slate-800 font-semibold py-2 px-4 border border-slate-300 rounded-full shadow-sm transition-colors duration-200">
                    {topic}
                  </a>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopicalClusters;
