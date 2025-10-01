'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Users, MessageSquare, FileText, Clock } from 'lucide-react';

const stats = [
  { id: 1, name: 'Active Users', value: '5K+', icon: Users },
  { id: 2, name: 'Registrations', value: '1K+', icon: Users },
  { id: 3, name: 'Quotes Generated', value: '10K+', icon: FileText },
  { id: 4, name: 'Avg. Response Time', value: '<2s', icon: Clock },
];

export default function StatsSection() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 }
    );

    const element = document.getElementById('stats-section');
    if (element) {
      observer.observe(element);
    }

    return () => {
      if (element) {
        observer.unobserve(element);
      }
    };
  }, []);

  return (
    <div id="stats-section" className="bg-gray-50 py-12 sm:py-16">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:max-w-none">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Trusted by businesses worldwide
            </h2>
            <p className="mt-4 text-lg leading-8 text-gray-600">
              Join thousands of satisfied users who have streamlined their business processes with us.
            </p>
          </div>
          
          <dl className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <motion.div
                key={stat.id}
                className="flex flex-col items-center"
                initial={{ opacity: 0, y: 20 }}
                animate={isVisible ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: stat.id * 0.1 }}
              >
                <div className="rounded-full bg-blue-100 p-3 text-blue-600">
                  <stat.icon className="h-6 w-6" aria-hidden="true" />
                </div>
                <dt className="mt-6 text-base font-semibold leading-7 text-gray-900">{stat.name}</dt>
                <dd className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
                  {stat.value}
                </dd>
              </motion.div>
            ))}
          </dl>
        </div>
      </div>
    </div>
  );
}
