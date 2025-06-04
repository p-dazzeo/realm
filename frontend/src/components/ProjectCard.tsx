
import React from 'react';
import { FileText } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ProjectCardProps {
  name: string;
  size: string;
  dateUploaded: string;
  onSelect?: () => void;
  isSelected?: boolean;
}

const ProjectCard = ({ name, size, dateUploaded, onSelect, isSelected }: ProjectCardProps) => {
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all duration-200 hover:shadow-md",
        isSelected
          ? "border-blue-500 bg-blue-50"
          : "hover:border-gray-300"
      )}
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-start space-x-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <FileText className="w-5 h-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">{name}</h3>
            <p className="text-sm text-gray-500 mt-1">Size: {size}</p>
            <p className="text-sm text-gray-500">Uploaded: {dateUploaded}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ProjectCard;
