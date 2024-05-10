import React, { useState, useEffect } from 'react';
import axios from 'axios';

const SampleAPI = () => {
  const [time, setTime] = useState(null);

  useEffect(() => {
    const fetchTime = async () => {
      try {
        const response = await axios.get('https://example.com/api/users?token=05ccb108154f4ec8ab1e9f13bfc58f529333acc2dfd2a2b5b1c71787b443aad2e285f1ea804899e9c12cb9124c60973');
      } catch (error) {
        console.error('Error fetching sample API:', error);
      }
    };

    fetchTime();

    return () => {
      setTime(null);
    };
  }, []);

  return (
    <div>
    </div>
  );
};

export default SampleAPI;
