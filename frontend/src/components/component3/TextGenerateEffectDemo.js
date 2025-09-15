import React from 'react';
import { TextGenerateEffect } from '../ui/text-generate-effect';

export default function TextGenerateEffectDemo(){
	return (
		<div className="p-4 text-center text-sm text-muted-foreground">
			<TextGenerateEffect words="Streaming bias significance chart" duration={0.4} />
		</div>
	);
}
