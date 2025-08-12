import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, FileText, Globe, Lightbulb, LineChart, Users } from "lucide-react";

const Features = () => {
  const features = [
    {
      icon: BarChart3,
      title: "Análise Preditiva",
      description: "Algoritmos avançados que antecipam riscos e tendências do mercado com alta precisão.",
      color: "text-primary"
    },
    {
      icon: LineChart,
      title: "Relatórios Inteligentes",
      description: "Dashboards interativos que transformam dados complexos em insights visuais claros.",
      color: "text-primary"
    },
    {
      icon: Globe,
      title: "Integração Global",
      description: "Conecta-se com diversas fontes de dados e sistemas existentes sem complicações.",
      color: "text-primary"
    },
    {
      icon: Users,
      title: "Colaboração em Equipe",
      description: "Ferramentas que facilitam o trabalho em grupo e tomada de decisões conjuntas.",
      color: "text-primary"
    },
    {
      icon: FileText,
      title: "Documentação Automática",
      description: "Gera relatórios e documentação automaticamente baseados nas análises realizadas.",
      color: "text-primary"
    },
    {
      icon: Lightbulb,
      title: "Insights Inteligentes",
      description: "Sugestões e recomendações baseadas em padrões identificados pela IA.",
      color: "text-primary"
    }
  ];

  return (
    <section id="funcionalidades" className="py-24 bg-gradient-subtle relative min-h-screen">
      {/* Debug indicator - remove later */}
      <div className="absolute top-4 right-4 bg-primary text-primary-foreground px-3 py-1 rounded text-sm z-10">
        Seção Funcionalidades
      </div>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground mb-6">
            Funcionalidades
            <span className="bg-gradient-simple bg-clip-text text-transparent ml-3">
              Poderosas
            </span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Tecnologia de ponta que simplifica processos complexos e potencializa seus resultados
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <Card 
                key={index} 
                className="group hover:shadow-simple transition-all duration-300 hover:-translate-y-2 border-border bg-card/50 backdrop-blur-sm"
              >
                <CardHeader className="text-center pb-4">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4 mx-auto group-hover:bg-primary/20 transition-colors">
                    <IconComponent className={`h-8 w-8 ${feature.color} group-hover:scale-110 transition-transform`} />
                  </div>
                  <CardTitle className="text-xl font-bold text-foreground group-hover:text-primary transition-colors">
                    {feature.title}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground text-center leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;