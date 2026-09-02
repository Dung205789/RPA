import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(201)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Ticket opened").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        actions.doubleClick(object7).perform();

        actions.sendKeys("Ask for more detail").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object8 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        object8.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object9 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        actions.doubleClick(object9).perform();

        actions.sendKeys("Can reproduce ?").perform();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[10]")).click();

        WebElement object14 = driver.findElement(By.xpath("//not-found"));
        object14.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object15 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(205)"));
        actions.doubleClick(object15).perform();

        actions.sendKeys("Read the report").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[9]")).click();

        WebElement object16 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(207)"));
        object16.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object17 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(207)"));
        actions.doubleClick(object17).perform();

        actions.sendKeys("Fix works ?").perform();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[10]")).click();

        WebElement object22 = driver.findElement(By.xpath("//not-found"));
        object22.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object27 = driver.findElement(By.xpath("//not-found"));
        object27.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object32 = driver.findElement(By.xpath("//not-found"));
        object32.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object33 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(209)"));
        actions.doubleClick(object33).perform();

        actions.sendKeys("Read the log file").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object38 = driver.findElement(By.xpath("//not-found"));
        object38.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object43 = driver.findElement(By.xpath("//not-found"));
        object43.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object48 = driver.findElement(By.xpath("//not-found"));
        object48.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object53 = driver.findElement(By.xpath("//not-found"));
        object53.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object58 = driver.findElement(By.xpath("//not-found"));
        object58.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object59 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(210)"));
        actions.doubleClick(object59).perform();

        actions.sendKeys("Reproduce the issue").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object64 = driver.findElement(By.xpath("//not-found"));
        object64.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object69 = driver.findElement(By.xpath("//not-found"));
        object69.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object74 = driver.findElement(By.xpath("//not-found"));
        object74.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object75 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(211)"));
        actions.doubleClick(object75).perform();

        actions.sendKeys("Find the cause").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object80 = driver.findElement(By.xpath("//not-found"));
        object80.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object81 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(212)"));
        actions.doubleClick(object81).perform();

        actions.sendKeys("Ticket resolved").perform();

        WebElement object82 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(202)"));
        WebElement relatedObject1 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object82, 0, object82.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object83 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        actions.moveToElement(object83, 0, object83.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object84 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object84, 0, object84.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object89 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object89).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("No");

        WebElement object90 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(203)"));
        WebElement relatedObject4 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(205)"));
        actions.moveToElement(object90, 0, object90.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object91 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(207)"));
        actions.doubleClick(object91).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object92 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(210)"));
        WebElement relatedObject5 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(211)"));
        actions.moveToElement(object92, 0, object92.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object93 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(211)"));
        WebElement relatedObject6 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(212)"));
        actions.moveToElement(object93, 0, object93.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object94 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(212)"));
        actions.doubleClick(object94).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Works");

        WebElement object95 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(213)"));
        WebElement relatedObject7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(217)"));
        actions.moveToElement(object95, 0, object95.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object100 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object100).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Still broken");

        WebElement object101 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(215)"));
        WebElement relatedObject8 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object101, 0, object101.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject8, 0, -relatedObject8.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object102 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(217)"));
        WebElement relatedObject9 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object102, 0, object102.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject9, 0, -relatedObject9.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object103 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject10 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object103, 0, object103.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject10, 0, -relatedObject10.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}