import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const Technology = () => {
  const techStack = [
    {
      category: "Backend & IA",
      technologies: [
        { name: "Python", description: "Linguagem principal para algoritmos de IA" },
        { name: "Scikit-learn", description: "Machine learning e análise preditiva" },
        { name: "Pandas", description: "Manipulação e análise de dados" },
        { name: "NumPy", description: "Computação científica e matemática" },
      ]
    },
    {
      category: "Frontend & Interface",
      technologies: [
        { name: "React", description: "Interface de usuário moderna e responsiva" },
        { name: "TypeScript", description: "Desenvolvimento tipado e seguro" },
        { name: "Tailwind CSS", description: "Design system consistente e elegante" },
        { name: "Vite", description: "Build rápido e desenvolvimento otimizado" },
      ]
    },
    {
      category: "Análise & Visualização",
      technologies: [
        { name: "Matplotlib", description: "Visualização de dados e gráficos" },
        { name: "Seaborn", description: "Gráficos estatísticos avançados" },
        { name: "Plotly", description: "Visualizações interativas" },
        { name: "Jupyter", description: "Desenvolvimento e prototipagem" },
      ]
    }
  ];

  return (
    <section id="tecnologia" className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
            Tecnologias
            <span className="bg-gradient-simple bg-clip-text text-transparent ml-3">
              Modernas
            </span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Stack tecnológico cuidadosamente selecionado para oferecer performance, 
            confiabilidade e escalabilidade
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {techStack.map((category, categoryIndex) => (
            <Card 
              key={categoryIndex} 
              className="bg-card/50 backdrop-blur-sm border-border hover:shadow-simple transition-all duration-300 hover:-translate-y-1"
            >
              <CardHeader className="text-center pb-4">
                <CardTitle className="text-xl font-bold text-foreground">
                  {category.category}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {category.technologies.map((tech, techIndex) => (
                  <div 
                    key={techIndex} 
                    className="group p-4 rounded-lg bg-background/50 border border-border/50 hover:border-primary/30 transition-all duration-200"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge 
                        variant="secondary" 
                        className="bg-primary/10 text-primary border-primary/20 group-hover:bg-primary/20 transition-colors"
                      >
                        {tech.name}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {tech.description}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-16 text-center">
          <Card className="bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5 border-primary/20 max-w-4xl mx-auto">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold text-foreground mb-4">
                Arquitetura Híbrida
              </h3>
              <p className="text-muted-foreground leading-relaxed mb-6">
                Combinamos o poder do Python para processamento de IA com uma interface web moderna, 
                criando uma experiência completa que funciona tanto como aplicação desktop quanto web.
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                <Badge variant="outline" className="border-primary/40 text-primary">
                  Cross-platform
                </Badge>
                <Badge variant="outline" className="border-primary/40 text-primary">
                  Scalable
                </Badge>
                <Badge variant="outline" className="border-primary/40 text-primary">
                  Open Source
                </Badge>
                <Badge variant="outline" className="border-primary/40 text-primary">
                  Modern Stack
                </Badge>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
};

export default Technology;