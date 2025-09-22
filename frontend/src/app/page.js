'use client';

import React from 'react';
import Hero from '@/components/Hero/Hero';
import Content from '@/components/Content/Content';

export default function Home() {
  return (
    <div style={{ flex: 1 }}>
      <Hero />
      <Content />
    </div>
  );
}