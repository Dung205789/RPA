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

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(218)"));
        actions.doubleClick(object1).perform();

        actions.sendKeys("Nightly timer fires").perform();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement object6 = driver.findElement(By.xpath("//not-found"));
        object6.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object7 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(3) > g:nth-child(1)"));
        actions.doubleClick(object7).perform();

        actions.sendKeys("Disk space free ?").perform();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[9]")).click();

        WebElement object12 = driver.findElement(By.xpath("//not-found"));
        object12.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object17 = driver.findElement(By.xpath("//not-found"));
        object17.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object18 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        actions.doubleClick(object18).perform();

        actions.sendKeys("Upload succeeded ?").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[1]")).click();

        WebElement object23 = driver.findElement(By.xpath("//not-found"));
        object23.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object28 = driver.findElement(By.xpath("//not-found"));
        object28.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object33 = driver.findElement(By.xpath("//not-found"));
        object33.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object38 = driver.findElement(By.xpath("//not-found"));
        object38.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object43 = driver.findElement(By.xpath("//not-found"));
        object43.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object44 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        actions.doubleClick(object44).perform();

        actions.sendKeys("List changed files").perform();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[10]")).click();

        WebElement object49 = driver.findElement(By.xpath("//not-found"));
        object49.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object54 = driver.findElement(By.xpath("//not-found"));
        object54.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object59 = driver.findElement(By.xpath("//not-found"));
        object59.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object64 = driver.findElement(By.xpath("//not-found"));
        object64.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object69 = driver.findElement(By.xpath("//not-found"));
        object69.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }

        WebElement object70 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        actions.doubleClick(object70).perform();

        actions.sendKeys("Read the file index").perform();

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object75 = driver.findElement(By.xpath("//not-found"));
        object75.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object80 = driver.findElement(By.xpath("//not-found"));
        object80.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object85 = driver.findElement(By.xpath("//not-found"));
        object85.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        WebElement object90 = driver.findElement(By.xpath("//not-found"));
        object90.click();
        Thread.sleep(500);
        for(int i=0; i<15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }

        WebElement object91 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        actions.doubleClick(object91).perform();

        actions.sendKeys("Backup complete").perform();

        WebElement object92 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(218)"));
        WebElement relatedObject1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(219)"));
        actions.moveToElement(object92, 0, object92.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject1, 0, -relatedObject1.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object93 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        WebElement relatedObject2 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(221)"));
        actions.moveToElement(object93, 0, object93.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject2, 0, -relatedObject2.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object98 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object98).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Full");

        WebElement object99 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(223)"));
        WebElement relatedObject3 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object99, 0, object99.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject3, 0, -relatedObject3.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object104 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object104).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Enough");

        WebElement object105 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject4 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object105, 0, object105.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject4, 0, -relatedObject4.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object110 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object110).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Yes");

        WebElement object111 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject5 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object111, 0, object111.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject5, 0, -relatedObject5.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object116 = driver.findElement(By.xpath("//not-found"));
        actions.doubleClick(object116).perform();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("Failed");

        WebElement object117 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject6 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object117, 0, object117.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject6, 0, -relatedObject6.getSize().getHeight() / 2)
                .release()
                .perform();

        WebElement object118 = driver.findElement(By.xpath("//not-found"));
        WebElement relatedObject7 = driver.findElement(By.xpath("//not-found"));
        actions.moveToElement(object118, 0, object118.getSize().getHeight() / 2)
                .clickAndHold()
                .moveToElement(relatedObject7, 0, -relatedObject7.getSize().getHeight() / 2)
                .release()
                .perform();

        driver.quit();
    }
}